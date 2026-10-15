from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect, text, or_
from controls.relay import control_appliance
import os, random, smtplib, datetime, math

app = Flask(__name__)
DEFAULT_PRESET_LIMIT = 500.0
PRESET_LIMIT_WATTS = DEFAULT_PRESET_LIMIT
DEFAULT_APPLIANCE_NAMES = ["Appliance 1", "Appliance 2", "Appliance 3"]
DEFAULT_APPLIANCE_CONFIGS = {
    "acu": {"display_name": "ACU Unit", "kw_limit": 10.0},
    "outlet": {"display_name": "3-Gang Outlet", "kw_limit": 5.0},
    "lighting": {"display_name": "Lighting Circuit", "kw_limit": 2.0},
}
APPLIANCE_NAMES = DEFAULT_APPLIANCE_NAMES.copy()
APPLIANCE_STATES = ["OFF", "OFF", "OFF"]
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'secret_key_here'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
# Pylance may complain about assignment types here; ignore the checker for this runtime assignment
login_manager.login_view = "login"  # type: ignore[assignment]

# ------------------ MODELS ------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100))
    birthday = db.Column(db.String(20))
    age = db.Column(db.Integer)
    address = db.Column(db.String(200))
    verified = db.Column(db.Boolean, default=False)
    def __init__(self, email: str, name: str | None = None, birthday: str | None = None, age: int | str | None = None, address: str | None = None, **kwargs):
        # Provide an explicit constructor so static checkers (Pylance) recognize these parameters
        super().__init__(**kwargs)
        self.email = email
        self.name = name
        self.birthday = birthday
        # allow None for age; accept string or int and coerce to int when possible
        coerced_age = None
        if age is not None and age != "":
            try:
                coerced_age = int(age)
            except Exception:
                coerced_age = None
        self.age = coerced_age
        self.address = address

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Log(db.Model):
    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    voltage = db.Column(db.Float)
    current = db.Column(db.Float)
    power = db.Column(db.Float)
    date_recorded = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship("User", backref=db.backref("logs", lazy=True))


class ApplianceConfig(db.Model):
    __tablename__ = "appliance_configs"

    id = db.Column(db.Integer, primary_key=True)
    appliance_key = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    kw_limit = db.Column(db.Float, default=10.0, nullable=False)
    is_tripped = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class PowerEvent(db.Model):
    __tablename__ = "power_events"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    value_watts = db.Column(db.Float, default=0.0)
    preset_limit = db.Column(db.Float, default=0.0)
    message = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def normalize_email(email):
    return email.strip().lower()


def convert_watts_to_kw(raw_watts):
    try:
        return float(raw_watts or 0.0) / 1000.0
    except (TypeError, ValueError):
        return 0.0


def convert_wh_to_kwh(raw_wh):
    try:
        return float(raw_wh or 0.0) / 1000.0
    except (TypeError, ValueError):
        return 0.0


def ensure_appliance_configs():
    for appliance_key, config in DEFAULT_APPLIANCE_CONFIGS.items():
        existing = ApplianceConfig.query.filter_by(appliance_key=appliance_key).first()
        if existing is None:
            db.session.add(ApplianceConfig(
                appliance_key=appliance_key,
                display_name=config["display_name"],
                kw_limit=float(config["kw_limit"]),
                is_tripped=False,
            ))
        else:
            existing.display_name = config["display_name"] if not existing.display_name else existing.display_name
            existing.kw_limit = float(config["kw_limit"]) if existing.kw_limit is None else existing.kw_limit
            existing.updated_at = datetime.datetime.utcnow()
    db.session.commit()


def get_appliance_configs():
    ensure_appliance_configs()
    entries = ApplianceConfig.query.order_by(ApplianceConfig.id).all()
    payload = {}
    for entry in entries:
        payload[entry.appliance_key] = {
            "display_name": entry.display_name,
            "kw_limit": float(entry.kw_limit or 0.0),
            "is_tripped": bool(entry.is_tripped),
        }
    for key, defaults in DEFAULT_APPLIANCE_CONFIGS.items():
        payload.setdefault(key, {
            "display_name": defaults["display_name"],
            "kw_limit": float(defaults["kw_limit"]),
            "is_tripped": False,
        })
    return payload


def normalize_appliance_states(states):
    if not isinstance(states, list):
        return None

    cleaned = []
    for item in states[:3]:
        value = str(item).strip().upper()
        if value in ("ON", "OFF"):
            cleaned.append(value)
        else:
            cleaned.append("OFF")

    while len(cleaned) < 3:
        cleaned.append("OFF")

    return cleaned[:3]


def migrate_legacy_tables():
    with app.app_context():
        tables = inspect(db.engine).get_table_names()
        if "user" in tables and "users" not in tables:
            db.session.execute(text("ALTER TABLE user RENAME TO users"))
            db.session.commit()


def send_verification_email(to_email, code):
    username = os.environ.get("MAIL_USERNAME")
    password = os.environ.get("MAIL_PASSWORD")

    if not username or not password:
        return False

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(username, to_email,
                f"Subject: Verify your account\n\nYour code is {code}")
        return True
    except Exception:
        return False


def send_reset_email(to_email, code):
    username = os.environ.get("MAIL_USERNAME")
    password = os.environ.get("MAIL_PASSWORD")

    if not username or not password:
        return False

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(username, to_email,
                f"Subject: Password Reset\n\nYour reset code is {code}")
        return True
    except Exception:
        return False

# ------------------ ROUTES ------------------
@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        email = normalize_email(request.form["email"])
        password = request.form["password"]
        confirm_password = request.form.get("confirm_password", "")
        name = request.form["name"]
        birthday = request.form["birthday"]
        age = request.form["age"]
        address = request.form["address"]

        if password != confirm_password:
            flash("Passwords do not match. Please re-enter both fields.")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists. Please log in or reset your password.")
            return redirect(url_for("login"))

        user = User(email=email, name=name, birthday=birthday, age=age, address=address)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        code = str(random.randint(100000,999999))
        session["verification_code"] = code
        session["pending_email"] = email

        email_sent = send_verification_email(email, code)
        if not email_sent:
            flash(f"Email not configured. Demo verification code: {code}.")
            return redirect(url_for("verify"))

        flash("Verification code sent to your email.")
        return redirect(url_for("verify"))
    return render_template("register.html")

@app.route("/verify", methods=["GET","POST"])
def verify():
    if request.method == "POST":
        code = request.form["code"]
        email = session.get("pending_email")
        user = User.query.filter_by(email=email).first() if email else None
        if code == session.get("verification_code"):
            if user:
                user.verified = True
                db.session.commit()
            else:
                flash("No pending user found for verification.")
            flash("Account verified! You can now login.")
            return redirect(url_for("login"))
        else:
            flash("Invalid code.")
    return render_template("verify.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = normalize_email(request.form["email"])
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and hasattr(user, "check_password") and user.check_password(password) and getattr(user, "verified", False):
            login_user(user)
            return redirect(url_for("dashboard"))
        elif user and not user.verified:
            flash("Account not verified yet. Check your email or use the demo code shown during registration.")
        else:
            flash("Invalid credentials or account not verified.")
    return render_template("login.html")

@app.route("/forgot", methods=["GET","POST"])
def forgot():
    if request.method == "POST":
        email = normalize_email(request.form["email"])
        user = User.query.filter_by(email=email).first()
        if user:
            code = str(random.randint(100000,999999))
            session["reset_code"] = code
            session["reset_email"] = email
            email_sent = send_reset_email(email, code)
            if not email_sent:
                flash(f"Email not configured. Demo reset code: {code}.")
                return redirect(url_for("reset"))
            flash("Reset code sent to your email.")
            return redirect(url_for("reset"))
    return render_template("forgot.html")

@app.route("/reset", methods=["GET","POST"])
def reset():
    if request.method == "POST":
        code = request.form["code"]
        new_password = request.form["password"]
        if code == session.get("reset_code"):
            email = session.get("reset_email")
            user = User.query.filter_by(email=email).first() if email else None
            if user:
                user.set_password(new_password)
                db.session.commit()
            else:
                flash("No user found for password reset.")
            flash("Password reset successful.")
            return redirect(url_for("login"))
        else:
            flash("Invalid reset code.")
    return render_template("forgot.html")

@app.route("/dashboard")
@login_required
def dashboard():
    logs = Log.query.filter(or_(Log.user_id == current_user.id, Log.user_id.is_(None))) \
        .order_by(Log.date_recorded.desc()).all()
    display_name = (current_user.name or current_user.email or "Admin").strip()
    if not display_name or display_name == "Admin":
        display_name = (current_user.email or "Admin").split("@", 1)[0].title()
    return render_template(
        "dashboard.html",
        logs=logs,
        appliance_names=APPLIANCE_NAMES,
        appliance_states=APPLIANCE_STATES,
        appliance_configs=get_appliance_configs(),
        user_display_name=display_name,
    )

@app.route("/set-preset", methods=["POST"])
@login_required
def set_preset():
    global PRESET_LIMIT_WATTS
    try:
        PRESET_LIMIT_WATTS = float(request.form.get("preset_limit", PRESET_LIMIT_WATTS))
    except ValueError:
        flash("Invalid power preset. Please enter a number.")
        return redirect(url_for("dashboard"))

    flash(f"Power limit set to {PRESET_LIMIT_WATTS} W.")
    return redirect(url_for("dashboard"))

@app.route("/api/control", methods=["GET", "POST"])
def api_control():
    global APPLIANCE_STATES

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        states = payload.get("appliances") or payload.get("appliance_states")
        normalized = normalize_appliance_states(states)
        if normalized is None:
            return jsonify({"error": "appliances must be a list of ON/OFF values"}), 400

        APPLIANCE_STATES = normalized
        for index, state in enumerate(APPLIANCE_STATES):
            try:
                control_appliance(index, state == "ON")
            except Exception:
                pass

        return jsonify({
            "appliances": APPLIANCE_STATES,
            "preset_limit": PRESET_LIMIT_WATTS,
            "appliance_names": APPLIANCE_NAMES,
            "status": "updated"
        })

    return jsonify({
        "appliances": APPLIANCE_STATES,
        "preset_limit": PRESET_LIMIT_WATTS,
        "appliance_names": APPLIANCE_NAMES
    })

@app.route("/api/data", methods=["POST"])
def api_data():
    """Accept a sensor batch from the Raspberry Pi and save usable readings."""
    payload = request.get_json(silent=True)
    readings = payload.get("readings") if isinstance(payload, dict) else payload
    if not isinstance(readings, list):
        return jsonify({"error": "request body must be a list of sensor readings"}), 400

    accepted = []
    for reading in readings:
        if not isinstance(reading, dict):
            continue

        try:
            voltage = float(reading["voltage"])
            current = float(reading["current"])
            power = float(reading["power"])
        except (KeyError, TypeError, ValueError):
            # PZEM errors and incomplete samples contain None values; skip them.
            continue

        if not all(math.isfinite(value) for value in (voltage, current, power)):
            continue

        accepted.append(Log(
            voltage=voltage,
            current=current,
            power=power,
        ))

    if not accepted:
        return jsonify({"error": "no readings contained valid voltage, current, and power values", "accepted": 0}), 400

    try:
        db.session.add_all(accepted)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to save incoming sensor readings")
        return jsonify({"error": "failed to save sensor readings"}), 500

    return jsonify({"status": "accepted", "accepted": len(accepted), "received": len(readings)}), 201

@app.route("/api/appliance-config", methods=["GET", "POST"])
def api_appliance_config():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return jsonify({"error": "payload must be an object"}), 400

        for appliance_key, config in payload.items():
            if not isinstance(config, dict):
                continue
            entry = ApplianceConfig.query.filter_by(appliance_key=appliance_key).first()
            if entry is None:
                entry = ApplianceConfig(
                    appliance_key=appliance_key,
                    display_name=str(config.get("display_name") or DEFAULT_APPLIANCE_CONFIGS.get(appliance_key, {}).get("display_name", appliance_key.title())),
                    kw_limit=float(config.get("kw_limit", DEFAULT_APPLIANCE_CONFIGS.get(appliance_key, {}).get("kw_limit", 0.0))),
                )
                db.session.add(entry)
            else:
                if "display_name" in config:
                    entry.display_name = str(config["display_name"]) or entry.display_name
                if "kw_limit" in config:
                    entry.kw_limit = float(config["kw_limit"])
                if "is_tripped" in config:
                    entry.is_tripped = bool(config["is_tripped"])
            entry.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        return jsonify({"configs": get_appliance_configs(), "status": "updated"})

    return jsonify({"configs": get_appliance_configs()})

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    global APPLIANCE_NAMES

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        names = payload.get("appliance_names")
        if not isinstance(names, list) or len(names) != 3:
            return jsonify({"error": "appliance_names must be a list of exactly 3 names"}), 400

        cleaned = []
        for item in names:
            cleaned.append(str(item).strip() or f"Appliance {len(cleaned) + 1}")

        APPLIANCE_NAMES = cleaned
        return jsonify({"appliance_names": APPLIANCE_NAMES, "status": "updated"})

    return jsonify({"appliance_names": APPLIANCE_NAMES})

@app.route("/api/preset", methods=["GET", "POST"])
def api_preset():
    global PRESET_LIMIT_WATTS

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        try:
            PRESET_LIMIT_WATTS = float(payload.get("preset_limit", PRESET_LIMIT_WATTS))
        except (TypeError, ValueError):
            return jsonify({"error": "preset_limit must be a number"}), 400
        return jsonify({"preset_limit": PRESET_LIMIT_WATTS, "status": "updated"})

    return jsonify({"preset_limit": PRESET_LIMIT_WATTS})

@app.route("/api/power-events", methods=["GET"])
def api_power_events():
    events = PowerEvent.query.order_by(PowerEvent.created_at.desc()).limit(20).all()
    payload = [{
        "id": event.id,
        "event_type": event.event_type,
        "value_watts": event.value_watts,
        "preset_limit": event.preset_limit,
        "message": event.message,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    } for event in events]
    return jsonify(payload)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

# ========== NEON ERROR HANDLERS ==========
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors with neon styling"""
    return render_template("error_404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with neon styling"""
    db.session.rollback()
    return render_template("error_500.html"), 500

@app.route("/loading")
def loading_screen():
    """Display loading screen - can be used during long operations"""
    return render_template("loading.html")

@app.route("/neon-demo")
def neon_demo():
    """Display neon effects showcase and demo page"""
    return render_template("neon_demo.html")

if __name__ == "__main__":
    with app.app_context():
        migrate_legacy_tables()
        db.create_all()
        ensure_appliance_configs()
    app.run(debug=True, host="0.0.0.0", port=5000)
