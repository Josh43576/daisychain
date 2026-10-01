# Type stubs for RPi.GPIO to satisfy Pylance in non-RaspberryPi environments
from typing import Any

BOARD: Any
BCM: Any
IN: Any
OUT: Any
HIGH: Any
LOW: Any


def setmode(mode: Any) -> None: ...


def setwarnings(value: bool) -> None: ...


def setup(pin: int, mode: Any, pull_up_down: Any = ..., initial: Any = ...) -> None: ...


def output(pin: int, value: Any) -> None: ...


def cleanup() -> None: ...
