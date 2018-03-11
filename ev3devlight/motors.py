"""Module for EV3 motors and mechanisms."""

from time import sleep
from .fileio import (read_int, read_str, write_int, write_str,
                     get_sensor_or_motor_path, write_duty)


class Motor():
    """
    Class for Medium/Large EV3 motor with an optional gear train.

    All positions (and speeds) are specified at the gear train output,
    in degrees (or degrees per second).

    When gear_ratio = 1, it's just a standard Medium/Large EV3 motor.

    """

    # The gear ratio is defined as the gear down factor, defined as follows:
    #
    #                       number of teeth on output gear
    # gear_ratio =  ---------------------------------------------
    #                number of teeth on the gear attached to motor
    #
    #
    # For example, consider the setup drawn below:
    #
    # Motor with 36t gear   12t gear on the output
    #       ____|_____        |
    #      /          \       |
    # ____/______      \    __|__
    #       /     \     \  /     \
    #      |   +   |    | |   +   |
    # ______\____ /     /  \_____/
    #     \            /
    #      \_________ /
    #
    # Here the gear ratio is 12t/36t = 1/3.
    def __init__(
            self,
            port,
            inverse_polarity=False,
            gear_ratio=1,
            setpoint_tolerance=5, max_speed=None):
        """Initialize a motor with specified direction and gear ratio."""
        # Get device path
        self.port = port
        self.path = get_sensor_or_motor_path('tacho-motor', self.port)

        # Open files for fast reading and writing
        self.position_file = open(self.path + '/position', 'r+b')
        self.speed_file = open(self.path + '/speed', 'rb')
        self.speed_sp_file = open(self.path + '/speed_sp', 'w')
        self.duty_sp_file = open(self.path + '/duty_cycle_sp', 'w')
        self.position_sp_file = open(self.path + '/position_sp', 'w')
        self.polarity_file = open(self.path + '/polarity', 'w')
        self.command_file = open(self.path + '/command', 'w')
        self.state_file = open(self.path + '/state', 'rb')

        # Reset any prior settings
        self.reset_all_settings()

        # Set chosen polarity
        if inverse_polarity:
            self.set_polarity_inversed()
        else:
            self.set_polarity_normal()

        # Store gear ratio: The number of output degrees for every motor degree
        self.gear_ratio = gear_ratio

        # Store set point tolerance: the mismatch that we allow when going to
        # targets. This is expressed in number of degrees at the mechanism
        # output.
        self.tolerance = setpoint_tolerance

        # Read the rated maximum speed of the motor
        with open(self.path + '/max_speed', 'rb') as f:
            self.RATED_MOTOR_MAX_SPEED = read_int(f)
            self.MAX_SPEED = self.RATED_MOTOR_MAX_SPEED/self.gear_ratio

        # Process the user specified maximum speed of the motor/mechanism, if
        # specified
        if max_speed is not None and max_speed < self.MAX_SPEED:
            self.MAX_SPEED = max_speed

    @property
    def position(self):
        """Get motor/mechanism position in degrees."""
        return read_int(self.position_file)/self.gear_ratio

    @position.setter
    def position(self, new_position):
        """Set motor/mechanism position in degrees."""
        write_int(self.position_file, new_position*self.gear_ratio)

    @property
    def speed(self):
        """Get the estimated speed of the motor/mechanism (deg/s)."""
        return read_int(self.speed_file)/self.gear_ratio

    def limit(self, speed):
        """Return a given speed value within the lower/upper bound."""
        return max(min(self.MAX_SPEED, speed), -1*self.MAX_SPEED)

    def run(self, speed):
        """Turn on the motor/mechanism at a given speed setpoint (deg/sec)."""
        limited_speed = self.limit(speed)
        write_int(self.speed_sp_file, limited_speed*self.gear_ratio)
        write_str(self.command_file, 'run-forever')

    def duty(self, duty):
        """Set the duty cycle."""
        write_duty(self.duty_sp_file, duty)

    def activate_duty_mode(self):
        """Activate duty cycle mode."""
        write_str(self.command_file, 'run-direct')

    def stop(self):
        """Stop the motor."""
        write_str(self.command_file, 'stop')

    def reset_all_settings(self):
        """Reset the motor."""
        write_str(self.command_file, 'reset')

    @property
    def stalled(self):
        """Check if motor is stalled."""
        return 'stalled' in self.state

    def wait_for_stalled(self):
        """Sleep until the motor is stalled."""
        while not self.stalled:
            sleep(0.001)

    def set_polarity_normal(self):
        """Set the motor polarity as standard."""
        write_str(self.polarity_file, 'normal')

    def set_polarity_inversed(self):
        """Set the motor polarity as the opposite of standard."""
        write_str(self.polarity_file, 'inversed')

    @property
    def state(self):
        """Get the motor state."""
        return read_str(self.state_file)

    @property
    def running(self):
        """Check if the motor is running."""
        return 'running' in self.state

    def at_target(self, target):
        """Check if motor is near the target within tolerance."""
        return target-self.tolerance <= self.position <= target+self.tolerance

    def go_to(self, target, speed, wait=True):
        """Go to a target at a desired speed."""
        if not self.running and not self.at_target(target):
            # Write target
            write_int(self.position_sp_file, target*self.gear_ratio)
            # Write speed setpoint
            absolute_speed = abs(self.limit(speed)*self.gear_ratio)
            write_int(self.speed_sp_file, absolute_speed)
            # Start moving
            write_str(self.command_file, 'run-to-abs-pos')
            # Wait for completion if requested
            if wait:
                while self.running:
                    pass


class DriveBase():
    """Control two motors to drive a skid steering robot."""

    def __init__(
            self,
            left_port,
            right_port,
            wheel_diameter,
            wheel_span,
            positive_turn_is_clockwise=True,
            max_speed=None,
            max_turn_rate=None,
            left_inverse_polarity=False,
            right_inverse_polarity=False,
            left_gear_ratio=1,
            right_gear_ratio=1):
        """Set up two motors."""
        # Store the maximum drive speed in cm/s and turnrate in deg/s
        self.max_speed = 100 if max_speed is None else max_speed
        self.max_turn_rate = 360 if max_turn_rate is None else max_turn_rate

        # Store which is the positive direction
        self.positive_turn_is_clockwise = positive_turn_is_clockwise

        # Math constants
        deg_per_rad = 180/3.1416

        # Compute radii
        wheel_radius = wheel_diameter/2
        wheel_base_radius = wheel_span/2

        # cm/s of forward travel for every 1 deg/s wheel rotation
        self.wheel_factor = wheel_radius / deg_per_rad

        # wheel speed (cm/s) for a desired rotation rate (deg/s) of the base
        self.base_factor = wheel_base_radius / deg_per_rad

        # Initialize motors
        self.left_motor = Motor(left_port,
                                left_inverse_polarity,
                                left_gear_ratio)
        self.right_motor = Motor(right_port,
                                 right_inverse_polarity,
                                 right_gear_ratio)

    def drive_and_turn(self, speed_cm_sec, turnrate_deg_sec):
        """Set speed of two motors at desired forward speed and turnrate."""
        # Wheel speed for given forward rate
        limited_speed = max(min(speed_cm_sec, self.max_speed), -self.max_speed)
        nett_speed = limited_speed / self.wheel_factor

        # Wheel speed for given turnrate
        limited_rate = max(min(turnrate_deg_sec, self.max_turn_rate),
                           -self.max_turn_rate)
        difference = limited_rate * self.base_factor / self.wheel_factor

        # Depending on sign of turnrate, go left or right
        if self.positive_turn_is_clockwise:
            left_speed = nett_speed + difference
            right_speed = nett_speed - difference
        else:
            left_speed = nett_speed - difference
            right_speed = nett_speed + difference

        # Apply the calculated speeds to the motor
        self.left_motor.run(left_speed)
        self.right_motor.run(right_speed)

    def stop(self):
        """Stop the robot by stopping motors."""
        self.left_motor.stop()
        self.right_motor.stop()


class Mechanism():
    """Mechanisms with a fixed stop and fixed targets."""

    def __init__(
            self,
            motor,
            targets,
            default_speed,
            touch_sensor=None,
            reset_immediately=True):
        """Initialize mechanism and reset it."""
        # Check that the reset target exists, and that is indeed either
        # the highest or lowest target
        assert targets['reset'] in \
            [max(targets.values()), min(targets.values())], \
            "Targets must include reset target"

        # Determine in which direction the reset target
        # is relative to all other targets
        if targets['reset'] == max(targets.values()):
            self.reset_forward = True
        else:
            self.reset_forward = False

        # Store the initialization arguments for later use
        self.motor = motor
        self.targets = targets
        self.default_speed = default_speed
        self.touch_sensor = touch_sensor

        # Reset the mechanism
        if reset_immediately:
            self.reset()

    def wait_for_stop(self):
        """Wait until motor is at the physical end point."""
        # Check if touch sensor was chosen as the reset switch
        if self.touch_sensor is not None:
            # If so, wait for the touch sensor to become pressed
            # by the mechanism
            self.touch_sensor.wait_for_press()
        else:
            # If there is no touch sensor, wait for the motor to stall
            self.motor.wait_for_stalled()

    def reset(self):
        """Reset the mechanism and encoder at the physical endpoint."""
        # Turn the motor on in the direction of the reset target
        if self.reset_forward:
            self.motor.run(self.default_speed)
        else:
            self.motor.run(-self.default_speed)

        # Wait for the motor to reach the reset
        self.wait_for_stop()
        self.motor.stop()

        # Set the current motor position equal to the reset target
        self.motor.position = self.targets['reset']

    def go_to_target(self, target, speed=None, wait=True):
        """Go to a previously defined named target."""
        # Select the speed
        if speed is None:
            speed = self.default_speed
        # Run the standard motor go to routine
        self.motor.go_to(self.targets[target], speed, wait)
