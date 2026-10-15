import unittest

from app import app, db


class ApiDataRouteTests(unittest.TestCase):
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

    def test_api_data_accepts_valid_readings(self):
        payload = {
            "readings": [
                {"slave_id": 1, "voltage": 220.5, "current": 1.2, "power": 264.6, "energy": 12.0},
                {"slave_id": 2, "voltage": 230.0, "current": 0.9, "power": 207.0, "energy": 3.0},
            ]
        }

        response = app.test_client().post("/api/data", json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn("accepted", response.get_json())


if __name__ == "__main__":
    unittest.main()
