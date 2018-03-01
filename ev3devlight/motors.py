import time
from .fileio import read_int, read_str, write_int, write_str, get_sensor_or_motor_path, write_duty

class Motor():
    """Class for Medium/Large EV3 motor with an optional gear train.

    All positions (and speeds) are specified at the gear train output, in degrees (or degrees per second).

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

    def __init__(self, port, inverse_polarity=False, gear_ratio=1, setpoint_tolerance=5, max_speed=None):
        """Initialize a motor with specified forward direction and gear ratio."""
        # Get device path
        self.port = port
        self.path = get_sensor_or_motor_path('tacho-motor', self.port)

        # Open files for fast reading and writing
        self.position_file = open(self.path + '/position', 'rb')
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

        # Store set point tolerance: the mismatch that we allow when going to targets
        # This is expressed in number of degrees at the mechanism output.
        self.setpoint_tolerance = setpoint_tolerance

        # Read the rated maximum speed of the motor
        with open(self.path + '/max_speed', 'rb') as f:
            self.RATED_MOTOR_MAX_SPEED = read_int(f)
            self.MAX_SPEED = self.RATED_MOTOR_MAX_SPEED/self.gear_ratio

        # Process the user specified maximum speed of the motor/mechanism, if specified
        if max_speed is not None and max_speed < self.MAX_SPEED:
            self.MAX_SPEED = max_speed

    @property
    def position(self):
        """Get motor/mechanism position in degrees"""
        return read_int(self.position_file)/self.gear_ratio

    @property
    def speed(self):
        """Get the estimated speed of the motor/mechanism in degrees per second"""
        return read_int(self.speed_file)/self.gear_ratio    

    def limit(self, speed):
        """Return a given speed value such that it is within the specified lower/upper bound"""
        return max(min(self.MAX_SPEED, speed), -1*self.MAX_SPEED)    

    def run(self, speed):
        """Turn on the motor/mechanism at a given speed setpoint in degrees per second"""
        scaled_speed = self.limit(speed*self.gear_ratio)
        write_int(self.speed_sp_file, scaled_speed)
        write_str(self.command_file, 'run-forever') 

    def duty(self, duty):
        write_duty(self.duty_sp_file, duty)       

    def activate_duty_mode(self):
        write_str(self.command_file, 'run-direct') 

    def stop(self):
        write_str(self.command_file, 'stop') 

    def reset_all_settings(self):
        write_str(self.command_file, 'reset')      

    def reset_encoder(self):
        pass       
        # TODO: reset encoder without altering other properties   

    # TODO: WAIT FOR STALLED

    def set_polarity_normal(self):
        write_str(self.polarity_file, 'normal')

    def set_polarity_inversed(self):
        write_str(self.polarity_file, 'inversed')        

    @property
    def state(self):
        return read_str(self.state_file)

    @property
    def running(self):
        return 'running' in self.state

    def at_target(self, target):
        """Return True when position is near the target with the specified tolerance"""
        return target - self.setpoint_tolerance <= self.position <= target + self.setpoint_tolerance

    def go_to(self, target, speed, wait=False):
        "Go to a target at a desired speed"
        if not self.running and not self.at_target(target):
            # Write target
            write_int(self.position_sp_file, target*self.gear_ratio) 
            # Write speed setpoint
            write_int(self.speed_sp_file, abs(self.limit(speed*self.gear_ratio))) 
            # Start moving
            write_str(self.command_file, 'run-to-abs-pos') 
            # Wait for completion if requested
            if wait:
                while self.running:
                    pass

class DriveBase:
    """Easily control two large motors to drive a skid steering robot using specified forward speed and turnrate"""

    def __init__(self, left_port,
                       right_port,
                       wheel_diameter,
                       wheel_span,                       
                       positive_turn_rate_means_clockwise=True,
                       max_speed=None,
                       max_turn_rate=None,                       
                       left_inverse_polarity=False,
                       right_inverse_polarity=False,
                       left_gear_ratio=1,
                       right_gear_ratio=1
                       ):
        """Set up two motors"""

        # Store the maximum drive speed in cm/s and turnrate in deg/s
        self.max_speed = max_speed if max_speed is not None else 100
        self.max_turn_rate = max_turn_rate if max_turn_rate is not None else 360

        # Store which is the positive direction
        self.positive_turn_rate_means_clockwise = positive_turn_rate_means_clockwise

        # Math constants
        deg_per_rad = 180/3.1416

        #Compute radii
        wheel_radius = wheel_diameter/2
        wheel_base_radius = wheel_span/2

        # cm/s of forward travel for every 1 deg/s wheel rotation
        self.wheel_cm_sec_per_deg_s = wheel_radius / deg_per_rad 

        # wheel speed (cm/s) for a desired rotation rate (deg/s) of the base
        self.wheel_cm_sec_per_base_deg_sec =  wheel_base_radius / deg_per_rad

        # Initialize motors
        self.left_motor = Motor(left_port, left_inverse_polarity, left_gear_ratio)
        self.right_motor = Motor(right_port, right_inverse_polarity, right_gear_ratio)

    def drive_and_turn(self, speed_cm_sec, turnrate_deg_sec):
        """Set speed of two motors to attain desired forward speed and turnrate"""

        # Wheel speed for given forward rate
        nett_speed = max(min(speed_cm_sec, self.max_speed), -self.max_speed) / self.wheel_cm_sec_per_deg_s

        # Wheel speed for given turnrate
        difference = max(min(turnrate_deg_sec, self.max_turn_rate), -self.max_turn_rate) * self.wheel_cm_sec_per_base_deg_sec / self.wheel_cm_sec_per_deg_s

        # Depending on sign of turnrate, go left or right
        if self.positive_turn_rate_means_clockwise:
            left_speed = nett_speed + difference
            right_speed = nett_speed - difference
        else:
            left_speed = nett_speed - difference
            right_speed = nett_speed + difference            

        # Apply the calculated speeds to the motor
        self.left_motor.run(left_speed)
        self.right_motor.run(right_speed)

    def stop(self):
        """Stop the robot"""
        # Stop robot by stopping motors
        self.left_motor.stop()
        self.right_motor.stop()    