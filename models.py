"""Compatibility exports for the application's single SQLAlchemy model registry."""
from app import ApplianceConfig, Log, PowerEvent, SystemSettings, User, VerificationCode, db

__all__ = [
    "db", "User", "Log", "ApplianceConfig", "PowerEvent",
    "SystemSettings", "VerificationCode",
]
