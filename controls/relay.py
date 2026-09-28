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
# Relay GPIOs (BCM): 17, 27, 22  — previously physical BOARD pins [11,13,15]
relay_pins = [17, 27, 22]

# Use BCM numbering consistently
GPIO.setmode(GPIO.BCM)
for pin in relay_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)  # Default OFF

__all__ = ["relay_pins", "control_appliance", "cleanup"]


def control_appliance(index, state: bool):
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
    GPIO.cleanup()