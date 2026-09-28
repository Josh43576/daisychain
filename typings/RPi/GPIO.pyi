# Type stubs for RPi.GPIO to satisfy Pylance in non-RaspberryPi environments
from typing import Any

BOARD: Any
BCM: Any
OUT: Any
HIGH: Any
LOW: Any

def setmode(mode: Any) -> None: ...

def setup(pin: int, mode: Any) -> None: ...

def output(pin: int, value: Any) -> None: ...

def cleanup() -> None: ...
