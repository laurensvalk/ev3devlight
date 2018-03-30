"""Module for EV3 Brick Buttons, LEDS, and Display."""
from sys import stderr
from .fileio import read_int, get_battery_path


def print_vscode(*args, **kwargs):
    """Print a message to standard error so it displays in the vscode IDE."""
    print(*args, file=stderr, **kwargs)


def print_display(*args, **kwargs):
    """Print a message on the EV3 display."""
    print(*args, **kwargs)


class Battery():
    """Read battery diagnostics."""

    def __init__(self):
        """Open battery diagnostic files."""
        path = get_battery_path()
        self.voltage_file = open(path + 'voltage_now', 'rb')

    @property
    def voltage(self):
        """Return battery voltage."""
        return read_int(self.voltage_file) / 1e6
    
# TODO: Set LEDS
