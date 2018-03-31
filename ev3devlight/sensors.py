"""Module for standard EV3 sensors."""

from .fileio import read_int, get_sensor_or_motor_path
from time import sleep


class Sensor(object):
    """Generic sensor class."""

    def __init__(self, port):
        """Initialize touch sensor."""
        self.port = port
        self.path = get_sensor_or_motor_path('lego-sensor', self.port)
        self.value0_file = self.open('value0')
        self.pause_time = 0.001

    def open(self, file_name):
        """Open file for fast reading."""
        return open(self.path + '/' + file_name, 'rb')

    @property
    def value0(self):
        """Return value0."""
        return read_int(self.value0_file)

    @property
    def mode(self):
        """Read sensor mode string."""
        with open(self.path + '/mode', 'r') as mode_file:
            return mode_file.read().strip()

    @mode.setter
    def mode(self, mode):
        """Write sensor mode string."""
        if self.mode != mode:
            # Write new mode only if it is different than the current one
            with open(self.path + '/mode', 'w') as mode_file:
                mode_file.write(mode)

    def pause(self):
        """Briefly do nothing."""
        sleep(self.pause_time)


class Touch(Sensor):
    """Configure Touch Sensor."""

    @property
    def pressed(self):
        """Return True if sensor is pressed, return False if released."""
        return bool(self.value0)

    @property
    def released(self):
        """Return True if sensor is released, return False if pressed."""
        return not self.pressed

    def wait_for_press(self):
        """Pause until the sensor is pressed."""
        while not self.pressed:
            self.pause()

    def wait_for_release(self):
        """Pause until the sensor is released."""
        while self.pressed:
            self.pause()

    def wait_for_bump(self):
        """Pause until the sensor is pressed and then released.

        If already pressed, then just wait for a release.
        """
        self.wait_for_press()
        self.wait_for_release()


class Gyro(Sensor):
    """Configure a Gyro sensor."""

    def __init__(self, port, read_rate=True, read_angle=False, calibrate=True):
        """Initialize sensor and set mode."""
        # Basic sensor initialization
        Sensor.__init__(self, port)

        # Assert that at least one read mode is specified
        assert read_rate or read_angle, "Select gyro rate, gyro angle, or both"

        # Calibrate if desired
        if calibrate:
            self.calibrate()

        # Set mode based on initialization arguments.
        # Then open relevant sensor files for fast reading.
        if read_rate and read_angle:
            self.mode = 'GYRO-G&A'
            self.angle_file = self.open('value0')
            self.rate_file = self.open('value1')
        elif read_angle:
            self.mode = 'GYRO-ANG'
            self.angle_file = self.open('value0')
        elif read_rate:
            self.mode = 'GYRO-RATE'
            self.rate_file = self.open('value0')

    def calibrate(self):
        """Reset angle and rate bias to zero."""
        # Read mode that the sensor is currently in
        old_mode = self.mode
        # Set to calibration mode
        self.mode = 'GYRO-CAL'
        # Return to the previously selected mode
        self.mode = old_mode

    @property
    def rate(self):
        """Return gyro rate."""
        return read_int(self.rate_file)

    @property
    def angle(self):
        """Return gyro angle."""
        return read_int(self.angle_file)


class Proximity(Sensor):
    """Configure an IR sensor in proximity mode."""

    def __init__(self, port, threshold=50):
        """Initialize sensor and set mode."""
        Sensor.__init__(self, port)
        self.mode = 'IR-PROX'
        self.threshold = threshold

    @property
    def proximity(self):
        """Return proximity value (0 = closest, 100 = farthest)."""
        return self.value0

    @property
    def detected(self):
        """Return True if detected object is closer than specified threshold.

        Return false otherwise
        """
        return True if self.proximity <= self.threshold else False

    def wait_for_detection(self):
        """Pause until the an object is detected."""
        while not self.detected:
            self.pause()


class Remote(Sensor):
    """Configure an IR sensor to read remote button status."""

    # Numbered list of possible button presses
    buttons = [
        'NONE',
        'LEFT_UP',
        'LEFT_DOWN',
        'RIGHT_UP',
        'RIGHT_DOWN',
        'BOTH_UP',
        'LEFT_UP_RIGHT_DOWN',
        'LEFT_DOWN_RIGHT_UP',
        'BOTH_DOWN',
        'BEACON',
        'BOTH_LEFT',
        'BOTH_RIGHT'
    ]

    def __init__(self, port):
        """Initialize sensor and set mode."""
        Sensor.__init__(self, port)
        self.mode = 'IR-REMOTE'

    @property
    def button(self):
        """Return name of remote button currently pressed."""
        return self.buttons[self.value0]

    def pressed(self, button):
        """Check if specified remote button is currently pressed."""
        return self.button == button
