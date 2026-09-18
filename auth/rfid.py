try:
    import RPi.GPIO as GPIO  # type: ignore
except ModuleNotFoundError:
    GPIO = None

try:
    from mfrc522 import SimpleMFRC522
except ModuleNotFoundError:
    class SimpleMFRC522:
        def read(self):
            print("RFID mock: no hardware detected. Returning default allowed access.")
            return (1234567890, "mock-card")

# Setup RFID reader
reader = SimpleMFRC522()

# Example list of authorized IDs (replace with your actual card IDs)
AUTHORIZED_IDS = [1234567890, 9876543210]

__all__ = ["check_user", "AUTHORIZED_IDS", "read_rfid_id", "is_authorized"]


def read_rfid_id():
    """Read a card and return the numeric RFID ID, or None if not available."""
    try:
        print("Place your RFID card...")
        card_id, text = reader.read()
        print(f"RFID detected: ID={card_id}, Text={text}")
        return int(card_id)
    except Exception as e:
        print("RFID error:", e)
        return None


def is_authorized(card_id):
    return card_id in AUTHORIZED_IDS


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
