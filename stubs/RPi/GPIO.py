# Minimal in-workspace stub for RPi.GPIO to satisfy Pylance in editors
BOARD = "BOARD"
BCM = "BCM"
IN = "IN"
OUT = "OUT"
HIGH = 1
LOW = 0


def setmode(mode):
    pass


def setwarnings(value):
    pass


def setup(pin, mode, pull_up_down=None, initial=None):
    pass


def output(pin, value):
    pass


def cleanup():
    pass
