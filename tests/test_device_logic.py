import unittest
from unittest.mock import patch

from main import apply_commands, update_daily_energy


class DeviceLogicTests(unittest.TestCase):
    def setUp(self):
        self.readings = [
            {"slave_id": 1, "power": 100.0, "energy": 1000.0},
            {"slave_id": 2, "power": 150.0, "energy": 2000.0},
            {"slave_id": 3, "power": 50.0, "energy": 500.0},
        ]
        self.commands = {"connected": True, "appliances": ["ON", "OFF", "ON"], "preset_limit": 1000.0}
        self.limits = {"acu": 2.0, "outlet": 2.0, "lighting": 2.0}

    def test_sensor_fault_fails_corresponding_channel_off(self):
        from main import reported_cutoffs
        reported_cutoffs.clear()
        broken = [dict(item) for item in self.readings]
        broken[0]["power"] = None
        with patch("main.control_appliance") as relay, patch("main.report_trip"):
            apply_commands(broken, self.commands, self.limits)
        relay.assert_any_call(0, False)

    def test_system_cap_forces_all_channels_off(self):
        from main import reported_cutoffs
        reported_cutoffs.clear()
        commands = dict(self.commands, preset_limit=200.0)
        with patch("main.control_appliance") as relay, patch("main.report_trip"):
            apply_commands(self.readings, commands, self.limits)
        relay.assert_any_call(0, False)
        relay.assert_any_call(1, False)
        relay.assert_any_call(2, False)

    def test_malformed_command_response_fails_all_channels_off(self):
        with patch("main.control_appliance") as relay:
            apply_commands(self.readings, {"connected": True, "appliances": ["ON"]}, self.limits)
        self.assertEqual(relay.call_count, 3)
        relay.assert_any_call(0, False)
        relay.assert_any_call(1, False)
        relay.assert_any_call(2, False)

    def test_daily_energy_uses_meter_deltas_and_rolls_over(self):
        state = {"date": "2026-10-16", "daily_energy_kwh": 0.1,
                 "last_energy_wh": {"1": 900.0, "2": 1800.0, "3": 400.0}}
        with patch("main._atomic_json_write"):
            result = update_daily_energy(self.readings, state, today="2026-10-16")
            self.assertAlmostEqual(result["daily_energy_kwh"], 0.5)
            next_day = update_daily_energy(self.readings, result, today="2026-10-17")
        self.assertEqual(next_day["daily_energy_kwh"], 0.0)


if __name__ == "__main__":
    unittest.main()
