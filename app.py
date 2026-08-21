from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect, text
import os, random, smtplib, datetime

app = Flask(__name__)
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
