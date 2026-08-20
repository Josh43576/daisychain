from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100))
    birthday = db.Column(db.String(20))   # store as string for simplicity
    age = db.Column(db.Integer)
    address = db.Column(db.String(200))
    verified = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """Hash and store a password securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a password against the stored hash."""
        return check_password_hash(self.password_hash, password)


class Log(db.Model):
    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    voltage = db.Column(db.Float)
    current = db.Column(db.Float)
    power = db.Column(db.Float)
    date_recorded = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationship back to user
    user = db.relationship("User", backref=db.backref("logs", lazy=True))
