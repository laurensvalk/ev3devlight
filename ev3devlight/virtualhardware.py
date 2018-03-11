"""Module to generate dummy EV3 hardware files."""


def make_files():
    """Generate dummy EV3 hardware files."""
    # This code generates dummy hardware files such that the code
    # can run on a PC, for easier debugging.
    from os import makedirs
    from os.path import dirname

    def write_file_contents(basepath, files_and_contents):
        """Write a dictionary of filename/contents pairs to files."""
        for file_name, content in files_and_contents.items():
            full_path = basepath + '/' + file_name
            makedirs(dirname(full_path), exist_ok=True)
            with open(full_path, "w") as dummy_file:
                dummy_file.write(content)

    # Dummy content
    na = 'n/a'

    # Dictionary of motor files and default content
    motor_files = {
        'address': na,
        'command': na,
        'commands': 'run-forever run-to-abs-pos \
                     run-to-rel-pos run-timed run-direct stop reset',
        'count_per_rot': '360',
        'driver_name': na,
        'duty_cycle': '0',
        'duty_cycle_sp': '0',
        'hold_pid/Kp': '0',
        'hold_pid/Ki': '0',
        'hold_pid/Kd': '0',
        'max_speed': '1560',
        'polarity': 'normal',
        'position': '0',
        'position_sp': '0',
        'ramp_down_sp': '0',
        'ramp_up_sp': '0',
        'speed': '0',
        'speed_pid/Kp': '0',
        'speed_pid/Ki': '0',
        'speed_pid/Kd': '0',
        'speed_sp': '0',
        'state': na,
        'stop_action': 'coast',
        'stop_actions': 'coast brake hold',
        'time_sp': '0'
    }

    # Dictionary of sensor files and default content
    sensor_files = {
        'address': na,
        'bin_data': na,
        'bin_data_format': 's8',
        'command': na,
        'commands': na,
        'decimals': '0',
        'driver_name': na,
        'fw_version': na,
        'mode': na,
        'modes': na,
        'num_values': '1',
        'poll_ms': na,
        'units': 'pct',
        'value0': '12',
        'value1': '0',
        'value2': '0',
        'value3': '0',
        'value4': '0',
        'value5': '0',
        'value6': '0',
        'value7': '0'
    }
    # Make 4 identical motor directories, except for the address file
    for id in range(4):
        motor_path = 'hardware/tacho-motor/motor' + str(id)
        motor_files['address'] = 'ev3-ports:out' + chr(ord('A')+id)
        write_file_contents(motor_path, motor_files)

    # Make 4 identical sensor directories, except for the address file
    for id in range(4):
        sensor_path = 'hardware/lego-sensor/sensor' + str(id)
        sensor_files['address'] = 'ev3-ports:in' + str(id+1)
        write_file_contents(sensor_path, sensor_files)

    # TODO: Populate dummy files for power supply, leds, buttons, etc
