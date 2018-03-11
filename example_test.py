#!/usr/bin/env micropython
"""Development/debug test program."""

from ev3devlight.motors import Motor, Mechanism
from ev3devlight.sensors import Touch
from time import sleep

# Set up devices
gripper_motor = Motor('outA', gear_ratio=12)
gripper_switch = Touch('in1')

# Define and reset mechanism
targets = {'open': 0, 'closed': 110, 'up': 400, 'reset': 430}
default_speed = 50
gripper = Mechanism(gripper_motor, targets, default_speed, gripper_switch)

# Go to predefined absolute target
gripper.go_to_target('closed')
sleep(1)
gripper.go_to_target('open')
