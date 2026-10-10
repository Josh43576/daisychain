import sys
import unittest
from unittest.mock import patch

from sensors.pzem import (
    PZEM_PORTS,
    PZEM_SLAVE_IDS,
    build_modbus_request,
    calculate_crc,
    validate_modbus_response,
)


class TestPzemModbus(unittest.TestCase):
    def test_slave_ids_are_present(self):
        self.assertEqual(PZEM_SLAVE_IDS, [1, 2, 3])

    def test_single_serial_port_bus_is_used(self):
        self.assertEqual(PZEM_PORTS, ["/dev/ttyUSB0"])

    def test_build_modbus_request_uses_slave_id(self):
        frame = build_modbus_request(2, 0x03, 0x0003, 2)
        self.assertEqual(frame[0], 2)
        self.assertEqual(frame[1], 0x03)
        self.assertEqual(frame[2], 0x00)
        self.assertEqual(frame[3], 0x03)
        self.assertEqual(frame[4], 0x00)
        self.assertEqual(frame[5], 0x02)
        self.assertEqual(len(frame), 8)

    def test_valid_crc_response_is_accepted(self):
        payload = b"\x00\x10\x00\x20"
        frame = b"\x02\x03\x04" + payload + calculate_crc(b"\x02\x03\x04" + payload)
        self.assertEqual(validate_modbus_response(frame, 0x03), payload)

    def test_exception_frame_is_rejected(self):
        frame = b"\x02\x83\x02" + calculate_crc(b"\x02\x83\x02")
        with self.assertRaises(ValueError):
            validate_modbus_response(frame, 0x03)

    def test_module_imports_without_serial_package(self):
        import importlib

        sys.modules.pop("sensors.pzem", None)
        with patch.dict(sys.modules, {"serial": None}):
            module = importlib.import_module("sensors.pzem")
            self.assertTrue(callable(module.calculate_crc))
            self.assertTrue(callable(module.build_modbus_request))
        sys.modules.pop("sensors.pzem", None)


if __name__ == "__main__":
    unittest.main()
