#!/usr/bin/env micropython
"""Example usage of ev3devlight."""

from ev3devlight.sensors import IRProximity
from ev3devlight.motors import Motor, DriveBase

# Set up IR Sensor to detect objects
eyes = IRProximity('in4', threshold=20)

# Set up a drivebase from two motors
base = DriveBase(left_port='outB',
                 right_port='outC',
                 wheel_diameter=3.5,
                 wheel_span=14.5)

# Make it move with a speed (cm/s) and turnrate (deg/s)
base.drive_and_turn(3, 0)

# Wait for an object
eyes.wait_for_detection()

# Stop the base
base.stop()

# Moving a motor
gripper = Motor('outA',
                inverse_polarity=True,
                gear_ratio=3,
                setpoint_tolerance=3)

# Move gripper
gripper.go_to(target=-90, speed=50, wait=True)
