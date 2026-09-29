try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    class _GPIO:
        BOARD = "BOARD"
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

# MPI3508 / Raspberry Pi relay wiring (BCM numbering)
# Physical pins: 11, 13, 15 = BCM 17, 27, 22
relay_pins = [17, 27, 22]

# Runtime initialization flag
_relays_initialized = False


def init(pins=None):
    """Initialize relay GPIOs at runtime. Call once on startup."""
    global _relays_initialized, relay_pins
    if pins is not None:
        relay_pins = pins

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        for pin in relay_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        _relays_initialized = True
        return True
    except Exception as e:
        print(f"Relay init failed: {e}")
        _relays_initialized = False
        return False


__all__ = ["relay_pins", "control_appliance", "cleanup", "init"]


def control_appliance(index, state: bool):
    try:
        if not _relays_initialized:
            init()

        if index < 0 or index >= len(relay_pins):
            print(f"Invalid appliance index: {index}")
            return False
        GPIO.output(relay_pins[index], GPIO.HIGH if state else GPIO.LOW)
        return True
    except Exception as e:
        print(f"Error controlling appliance {index}: {e}")
        return False


def cleanup():
    try:
        GPIO.cleanup()
    finally:
        global _relays_initialized
        _relays_initialized = False