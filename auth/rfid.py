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

__all__ = ["check_user", "AUTHORIZED_IDS"]


def check_user():
    """
    Reads an RFID card and checks if the ID is authorized.
    Returns True if authorized, False otherwise.
    """
    try:
        print("Place your RFID card...")
        card_id, text = reader.read()
        print(f"RFID detected: ID={card_id}, Text={text}")

        if card_id in AUTHORIZED_IDS:
            print("Access granted.")
            return True
        else:
            print("Access denied.")
            return False
    except Exception as e:
        print("RFID error:", e)
        return False
