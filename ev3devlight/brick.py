"""Module for EV3 Brick Buttons, LEDS, and Display."""
from sys import stderr


def print_vscode(*args, **kwargs):
    """Print a message to standard error so it displays in the vscode IDE."""
    print(*args, file=stderr, **kwargs)


def print_display(*args, **kwargs):
    """Print a message on the EV3 display."""
    print(*args, **kwargs)

# TODO: Read Battery Voltage
# TODO: Set LEDS
