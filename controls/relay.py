try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    class _GPIO:
        BCM = "BCM"
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

# Define GPIO pins for 3 SSR relays
relay_pins = [17, 27, 22]  # Adjust if you wire differently

# Setup GPIO mode
GPIO.setmode(GPIO.BCM)
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
