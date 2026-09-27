#!/usr/bin/env python3
"""Read multiple PZEM-004T modules on a shared Modbus RTU serial bus.

This script is designed for a Raspberry Pi using the `minimalmodbus` library.
Each PZEM has a unique Modbus slave ID and is read one by one.

Example usage:
    python pzem_multi_reader.py
"""

import time
import minimalmodbus

# ----------------------
# Configuration
# ----------------------
SERIAL_PORT = "/dev/ttyUSB0"   # Change to "/dev/ttyS0" if needed
BAUDRATE = 9600
PARITY = "N"
STOPBITS = 1
BYTESIZE = 8
TIMEOUT = 1.0

# Each PZEM device has a unique Modbus slave ID.
# Add or remove IDs as needed.
PZEM_IDS = [1, 2, 3]

# ----------------------
# Helper functions
# ----------------------

def create_instrument(slave_id: int, port: str = SERIAL_PORT):
    """Create a minimalmodbus instrument for one PZEM module."""
    instrument = minimalmodbus.Instrument(port, slave_id)
    instrument.serial.baudrate = BAUDRATE
    instrument.serial.bytesize = BYTESIZE
    instrument.serial.parity = PARITY
    instrument.serial.stopbits = STOPBITS
    instrument.serial.timeout = TIMEOUT
    return instrument


def read_voltage(instrument) -> float:
    """Read voltage in volts (1 decimal place)."""
    return instrument.read_register(0x0000, 1, 4) / 10.0


def read_current(instrument) -> float:
    """Read current in amps (3 decimal places)."""
    # PZEM uses two registers to store a 32-bit value.
    # Combined register values are read as a 32-bit integer, then scaled.
    low = instrument.read_register(0x0001, 0, 4)
    high = instrument.read_register(0x0002, 0, 4)
    raw = (high << 16) | low
    return raw / 1000.0


def read_power(instrument) -> float:
    """Read power in watts (1 decimal place)."""
    low = instrument.read_register(0x0003, 0, 4)
    high = instrument.read_register(0x0004, 0, 4)
    raw = (high << 16) | low
    return raw / 10.0


def read_energy(instrument) -> float:
    """Read energy in Wh (0 decimal places)."""
    low = instrument.read_register(0x0005, 0, 4)
    high = instrument.read_register(0x0006, 0, 4)
    raw = (high << 16) | low
    return float(raw)


def read_pzem_module(slave_id: int):
    """Read one PZEM module and return a dictionary with telemetry data."""
    instrument = create_instrument(slave_id)

    result = {
        "slave_id": slave_id,
        "voltage": None,
        "current": None,
        "power": None,
        "energy": None,
        "error": None,
    }

    try:
        result["voltage"] = read_voltage(instrument)
    except Exception as exc:
        result["error"] = f"Voltage read failed: {exc}"

    try:
        result["current"] = read_current(instrument)
    except Exception as exc:
        if result["error"] is None:
            result["error"] = f"Current read failed: {exc}"
        else:
            result["error"] += f" | Current read failed: {exc}"

    try:
        result["power"] = read_power(instrument)
    except Exception as exc:
        if result["error"] is None:
            result["error"] = f"Power read failed: {exc}"
        else:
            result["error"] += f" | Power read failed: {exc}"

    try:
        result["energy"] = read_energy(instrument)
    except Exception as exc:
        if result["error"] is None:
            result["error"] = f"Energy read failed: {exc}"
        else:
            result["error"] += f" | Energy read failed: {exc}"

    return result


def print_module_data(data):
    """Print telemetry for one module in a clear format."""
    print(f"\n--- PZEM Slave ID {data['slave_id']} ---")
    if data["error"]:
        print(f"ERROR: {data['error']}")
        return

    print(f"Voltage: {data['voltage']:.1f} V")
    print(f"Current: {data['current']:.3f} A")
    print(f"Power:   {data['power']:.1f} W")
    print(f"Energy:  {data['energy']:.0f} Wh")


def main():
    """Read all configured PZEM modules in sequence."""
    print(f"Opening Modbus serial bus on {SERIAL_PORT}")
    print(f"Reading PZEM slave IDs: {PZEM_IDS}")

    while True:
        print("\n=== Reading cycle ===")
        for slave_id in PZEM_IDS:
            try:
                reading = read_pzem_module(slave_id)
                print_module_data(reading)
            except Exception as exc:
                print(f"\n--- PZEM Slave ID {slave_id} ---")
                print(f"UNHANDLED ERROR: {exc}")

        time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping PZEM reader.")
