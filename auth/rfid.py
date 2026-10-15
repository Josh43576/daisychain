import os
import time

try:
    import RPi.GPIO as GPIO  # type: ignore
except ModuleNotFoundError:
    GPIO = None

if os.environ.get("SIMULATE_HARDWARE") == "1":
    GPIO = None

try:
    from mfrc522 import SimpleMFRC522
except ModuleNotFoundError:
    SimpleMFRC522 = None

if os.environ.get("SIMULATE_HARDWARE") == "1":
    SimpleMFRC522 = None


class _SimulatedRFIDReader:
    def read(self):
        card_id = int(os.environ.get("SIMULATED_RFID_ID", "1234567890"))
        print("SIMULATION ONLY: returning configured simulated RFID ID")
        return card_id, "simulation"

# Lazy reader instance; initialization deferred to runtime to avoid import-time SPI errors
reader = None
RFID_RESET_TIMEOUT_SECONDS = 5.0
rfid_state = {
    "mode": "NORMAL_MONITORING",
    "armed_pin": None,
    "armed_since": 0.0,
}


def init_reader():
    """Initialize the MFRC522 reader. Call at runtime when SPI is ready."""
    global reader
    if reader is not None:
        return True
    if SimpleMFRC522 is None:
        if os.environ.get("SIMULATE_HARDWARE") == "1":
            reader = _SimulatedRFIDReader()
            return True
        print("RFID library unavailable; access will fail closed.")
        return False
    try:
        reader = SimpleMFRC522()
        return True
    except Exception as e:
        print(f"RFID init failed: {e}")
        reader = None
        return False

# Authorized RFID card IDs
AUTHORIZED_IDS = [1234567890, 9876543210, 350602620437]
__all__ = [
    "check_user",
    "AUTHORIZED_IDS",
    "read_rfid_id",
    "is_authorized",
    "RFID_RESET_TIMEOUT_SECONDS",
    "rfid_state",
    "process_rfid_reset_state",
    "get_tripped_appliance_pins",
]


def read_rfid_id():
    """Read a card and return the numeric RFID ID, or None if not available."""
    try:
        if reader is None:
            if not init_reader():
                print("RFID hardware not available.")
                return None

        card_id, text = reader.read()
        print(f"RFID detected: ID={card_id}, Text={text}")
        return int(card_id)
    except Exception as e:
        print("RFID error:", e)
        return None


def is_authorized(card_id):
    return card_id in AUTHORIZED_IDS


def set_gpio_pin_state(pin, high):
    """Drive a Pi GPIO pin to HIGH or LOW when GPIO is available."""
    if GPIO is None:
        return False
    try:
        GPIO.output(pin, GPIO.HIGH if high else GPIO.LOW)
        return True
    except Exception:
        return False


def get_tripped_appliance_pins(pins=None):
    """Return all tripped appliance pins currently being held LOW."""
    if GPIO is None:
        return []
    candidate_pins = pins or [17, 27, 22]
    tripped = []
    for pin in candidate_pins:
        try:
            if GPIO.input(pin) == GPIO.LOW:
                tripped.append(pin)
        except Exception:
            continue
    return tripped


def process_rfid_reset_state(pins=None):
    """Standalone two-scan reset state machine for tripped appliance pins."""
    global rfid_state
    card_id = read_rfid_id()
    if card_id is None or not is_authorized(card_id):
        return False

    candidate_pins = pins or [17, 27, 22]
    tripped_pins = get_tripped_appliance_pins(candidate_pins)

    if not tripped_pins:
        return False

    current_time = time.monotonic()
    if rfid_state["mode"] == "WAITING_FOR_CONFIRMATION":
        if rfid_state["armed_pin"] in tripped_pins:
            if current_time - rfid_state["armed_since"] <= RFID_RESET_TIMEOUT_SECONDS:
                set_gpio_pin_state(rfid_state["armed_pin"], True)
                print(f"RFID reset confirmed for pin {rfid_state['armed_pin']}. Power restored.")
                rfid_state["mode"] = "NORMAL_MONITORING"
                rfid_state["armed_pin"] = None
                rfid_state["armed_since"] = 0.0
                return True
            rfid_state["mode"] = "NORMAL_MONITORING"
            rfid_state["armed_pin"] = None
            rfid_state["armed_since"] = 0.0

    rfid_state["mode"] = "WAITING_FOR_CONFIRMATION"
    rfid_state["armed_pin"] = tripped_pins[0]
    rfid_state["armed_since"] = current_time
    print(f"RFID armed for pin {rfid_state['armed_pin']}. Scan again within {RFID_RESET_TIMEOUT_SECONDS}s to reset.")
    return False


def check_user():
    """
    Reads an RFID card and checks if the ID is authorized.
    Returns True if authorized, False otherwise.
    """
    card_id = read_rfid_id()
    if card_id is None:
        return False

    if is_authorized(card_id):
        print("Access granted.")
        return True

    print("Access denied.")
    return False
