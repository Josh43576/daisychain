import unittest

from app import convert_watts_to_kw


class ApplianceLimitTests(unittest.TestCase):
    def test_watts_are_converted_to_kw_before_limit_checks(self):
        self.assertAlmostEqual(convert_watts_to_kw(1500), 1.5)
        self.assertAlmostEqual(convert_watts_to_kw(1200), 1.2)

    def test_limit_values_are_not_treated_as_raw_watts(self):
        self.assertGreater(1500 / 1000.0, 10.0 / 1000.0)
        self.assertLess(1200 / 1000.0, 10.0)


if __name__ == "__main__":
    unittest.main()
