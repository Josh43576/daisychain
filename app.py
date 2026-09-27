from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect, text
import os, random, smtplib, datetime

app = Flask(__name__)
DEFAULT_PRESET_LIMIT = 500.0
PRESET_LIMIT_WATTS = DEFAULT_PRESET_LIMIT
DEFAULT_APPLIANCE_NAMES = ["Appliance 1", "Appliance 2", "Appliance 3"]
APPLIANCE_NAMES = DEFAULT_APPLIANCE_NAMES.copy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'secret_key_here'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

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
        user = User.query.filter_by(email=email).first()
        if code == session.get("verification_code"):
            user.verified = True
            db.session.commit()
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
        if user and user.check_password(password) and user.verified:
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
            user = User.query.filter_by(email=email).first()
            user.set_password(new_password)
            db.session.commit()
            flash("Password reset successful.")
            return redirect(url_for("login"))
        else:
            flash("Invalid reset code.")
    return render_template("forgot.html")

@app.route("/dashboard")
@login_required
def dashboard():
    logs = Log.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", logs=logs)

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

@app.route("/api/control", methods=["GET"])
def api_control():
    return jsonify({
        "appliances": ["OFF", "OFF", "OFF"],
        "preset_limit": PRESET_LIMIT_WATTS,
        "appliance_names": APPLIANCE_NAMES
    })

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
            label = str(item).strip()
            if not label:
                label = f"Appliance {len(cleaned) + 1}"
            cleaned.append(label)

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
    app.run(debug=True, host="0.0.0.0", port=5000)
