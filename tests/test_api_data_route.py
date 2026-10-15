import unittest

from app import app, db


class ApiDataRouteTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app_context = app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_api_data_accepts_valid_readings(self):
        payload = {
            "readings": [
                {"voltage": 220.5, "current": 1.2, "power": 264.6},
                {"voltage": 230.0, "current": 0.9, "power": 207.0},
            ]
        }

        response = app.test_client().post("/api/data", json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn("accepted", response.get_json())


if __name__ == "__main__":
    unittest.main()
