from sys import stderr

def print_vscode(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

def print_display(*args, **kwargs):
    print(*args, **kwargs)

# TODO: Read Battery Voltage
# TODO: Set LEDS