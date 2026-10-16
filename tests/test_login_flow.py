import re
import unittest
from unittest.mock import patch

from app import User, app, db


class LoginFlowTests(unittest.TestCase):
    def setUp(self):
        self.old_testing = app.config.get("TESTING", False)
        self.old_database_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app_context = app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()
        app.config["TESTING"] = self.old_testing
        app.config["SQLALCHEMY_DATABASE_URI"] = self.old_database_uri

    def test_verified_user_can_login_and_open_dashboard(self):
        user = User(email="test@example.com", name="Test User", is_admin=True)
        user.set_password("test-password-123")
        user.verified = True
        db.session.add(user)
        db.session.commit()

        client = app.test_client()
        login_page = client.get("/login")
        csrf_token = re.search(rb'name="csrf_token" value="([^"]+)"', login_page.data).group(1).decode()
        response = client.post("/login", data={
            "email": "TEST@example.com",
            "password": "test-password-123",
            "csrf_token": csrf_token,
        })

        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard", response.headers["Location"])
        dashboard = client.get("/dashboard")
        self.assertEqual(dashboard.status_code, 200)

    def test_local_registration_without_smtp_can_verify_and_login(self):
        client = app.test_client()
        register_page = client.get("/register")
        csrf_token = re.search(rb'name="csrf_token" value="([^"]+)"', register_page.data).group(1).decode()
        registration = {
            "email": "new@example.com",
            "password": "test-password-123",
            "confirm_password": "test-password-123",
            "name": "New User",
            "csrf_token": csrf_token,
        }
        with patch("app.send_verification_email", return_value=False), patch.dict("os.environ", {"ALLOW_DEMO_CODES": "1"}):
            response = client.post("/register", data=registration)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/verify", response.headers["Location"])

            verify_page = client.get("/verify")
            code_match = re.search(rb"Demo verification code: (\d{6})\.", verify_page.data)
            self.assertIsNotNone(code_match)
            verify_csrf = re.search(rb'name="csrf_token" value="([^"]+)"', verify_page.data).group(1).decode()
            verified = client.post("/verify", data={"code": code_match.group(1).decode(), "csrf_token": verify_csrf})
            self.assertEqual(verified.status_code, 302)

        login_page = client.get("/login")
        login_csrf = re.search(rb'name="csrf_token" value="([^"]+)"', login_page.data).group(1).decode()
        login = client.post("/login", data={
            "email": "new@example.com",
            "password": "test-password-123",
            "csrf_token": login_csrf,
        })
        self.assertEqual(login.status_code, 302)
        self.assertIn("/dashboard", login.headers["Location"])


if __name__ == "__main__":
    unittest.main()
