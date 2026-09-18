try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    class _GPIO:
        BOARD = "BOARD"
        OUT = "OUT"
        HIGH = 1
        LOW = 0

        @staticmethod
        def setmode(mode):
            pass

        @staticmethod
        def setup(pin, mode):
            pass

        @staticmethod
        def output(pin, value):
            pass

        @staticmethod
        def cleanup():
            pass

    GPIO = _GPIO()

# MPI3508 / Raspberry Pi physical pin numbering
# These are the relay control pins used for the appliance outputs.
relay_pins = [11, 13, 15]  # physical pins 11, 13, 15

# Use BOARD numbering to match your MPI3508 header wiring.
GPIO.setmode(GPIO.BOARD)
for pin in relay_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)  # Default OFF

__all__ = ["relay_pins", "control_appliance", "cleanup"]


def control_appliance(index, state: bool):
    """
    Control a specific appliance relay.
    index: 0, 1, or 2 (for Appliance 1, 2, 3)
    state: True = ON, False = OFF
    """
    try:
        if index < 0 or index >= len(relay_pins):
            print(f"Invalid appliance index: {index}")
            return False
        GPIO.output(relay_pins[index], GPIO.HIGH if state else GPIO.LOW)
        return True
    except Exception as e:
        print(f"Error controlling appliance {index}: {e}")
        return False


def cleanup():
    """Reset GPIO pins when shutting down."""
    GPIO.cleanup()
