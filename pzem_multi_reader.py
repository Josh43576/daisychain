#!/usr/bin/env python3
"""Read multiple PZEM-004T modules on a shared Modbus RTU serial bus.

This script is designed for a Raspberry Pi using the `minimalmodbus` library.
Each PZEM has a unique Modbus slave ID and is read one by one.

Example usage:
    python pzem_multi_reader.py
"""

import os
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

# Optional RS485 DE/RE drive pin. Set RS485_DE_RE_PIN from the environment
# when a hardware transceiver exposes a control GPIO. If not configured,
# the code falls back to the normal UART A/B wiring used by the adapter.
RS485_DE_RE_PIN = None
pin_value = os.environ.get("RS485_DE_RE_PIN")
if pin_value:
    try:
        RS485_DE_RE_PIN = int(pin_value)
    except ValueError:
        RS485_DE_RE_PIN = None


def set_rs485_direction(transmit: bool):
    """Enable the RS485 transmitter for writes and receiver mode for reads."""
    if RS485_DE_RE_PIN is None:
        return
    try:
        import RPi.GPIO as GPIO  # type: ignore

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RS485_DE_RE_PIN, GPIO.OUT)
        GPIO.output(RS485_DE_RE_PIN, GPIO.HIGH if transmit else GPIO.LOW)
    except Exception:
        pass


# Each PZEM device has a unique Modbus slave ID.
# Add or remove IDs as needed.
PZEM_IDS = [1, 2, 3]

# ----------------------
# Helper functions
# ----------------------

def create_instrument(slave_id: int, port: str = SERIAL_PORT):
    """Create a minimalmodbus instrument for one PZEM module."""
    instrument = minimalmodbus.Instrument(port, slave_id, mode=minimalmodbus.MODE_RTU)
    instrument.serial.baudrate = BAUDRATE
    instrument.serial.bytesize = BYTESIZE
    instrument.serial.parity = PARITY
    instrument.serial.stopbits = STOPBITS
    instrument.serial.timeout = TIMEOUT
    instrument.close_port_after_each_call = True
    return instrument


def read_voltage(instrument) -> float:
    """Read voltage in volts (1 decimal place)."""
    return instrument.read_input_register(0x0000, 1) / 10.0


def read_current(instrument) -> float:
    """Read current in amps (3 decimal places)."""
    return instrument.read_input_registers(0x0001, 2)[0] / 1000.0


def read_power(instrument) -> float:
    """Read power in watts (1 decimal place)."""
    raw = instrument.read_long(0x0003, functioncode=4, signed=False)
    return raw / 10.0


def read_energy(instrument) -> float:
    """Read energy in Wh (0 decimal places)."""
    return float(instrument.read_long(0x0005, functioncode=4, signed=False))


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
