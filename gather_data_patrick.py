import os
import sys
import time
import pandas as pd
from DIPPID import SensorUDP

DURATION = 10  # seconds per recording


PORT = 5700
sensor = SensorUDP(PORT)

time.sleep(2)

print(sensor.get_capabilities())

if not sensor.has_capability('accelerometer'):
    raise IOError('The sensor you want to use does not offer adequate capabilities, missing accelerometer')
if not sensor.has_capability('gyroscope'):
    raise IOError('The sensor you want to use does not offer adequate capabilities, missing gyroscope')


# Create data dir if not exists (Line recommended by chatGPT)
os.makedirs('data', exist_ok=True)

# Name selection for user
name = 'patrick'
if name is None:
    name = input('Please enter your name (or edit it in the file and rerun to skip this step later): ').lower().strip()


sampling_rate = None
# Choose a sampling rate
print('1) 20Hz')
print('2) 100Hz')

sampling_rate_input = input('Use 1 or 2 to choose a sampling rate: ')
sampling_rate = 20 if sampling_rate_input == '1' else 100

activity = None
# Choose an activity
print('1) Jumping Jacks')
print('2) Lifting')
print('3) Rowing')
print('4) Running')

activity_input = input('Use 1 - 4 to choose your activity: ')

if activity_input == '1':
    activity = 'jumpingjack'
elif activity_input == '2':
    activity = 'lifting'
elif activity_input == '3':
    activity = 'rowing'
elif activity_input == '4':
    activity = 'running'

placement = None
# Choose a sensor placement
print('1) Hand')
print('2) Pocket')

placement_input = input('Use 1 or 2 to choose your placement: ')

placement = 'hand' if placement_input == '1' else 'pocket'

def build_filename(_name, _activity, _sampling_rate, _placement, _recording_num):
    return f"{_name}_{_activity}_{_sampling_rate}hz_{_placement}_{_recording_num}.csv"


def get_recording_num(_name, _activity, _sampling_rate, _placement):
    # List all files in data dir
    files = os.listdir('data')
    # Select only these where name, activity, sampling rate and placement match
    relevant = [f for f in files if _name in f and _activity in f and str(_sampling_rate) in f and _placement in f]
    # Return len of relevant files + 1 to start indexing at 1
    return len(relevant) + 1

# OLD lines were what I originally had and was rewritten by chatGPT
#OLD: if any([name, activity, sampling_rate, placement]) is None:
if None in [name, activity, sampling_rate, placement]:
    raise ValueError("There is an invalid value for at least one of the selections, please try again")

print(f'Your selection: {name}, {sampling_rate}, {activity}, {placement}')
cont = input('Continue with these settings? (y/n): ')
if cont.lower() == 'n':
    print("Exiting...")
    sys.exit()

recording_num = get_recording_num(name, activity, sampling_rate, placement)
if recording_num > 5:
    exceed_limit = input('You already recorded 5 samples for this setup; Continue anyway? [y/n]')
    if exceed_limit.lower() == 'n':
        print("Exiting...")
        sys.exit()

filename = build_filename(name, activity, sampling_rate, placement, recording_num)

csv = 'id,timestamp,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z\n'
data_id = 0

print('Press button 1 on the DIPPID sender to start recording. After pressing you will have 3 seconds to get started.')


run_time = 0
# Pause time for correct sampling rate
pause_time = 1 / sampling_rate
#start_time = time.time()
#last_recorded_time = start_time
on_hold = True

while run_time < DURATION:

    # Messy block at the beginning
    while on_hold:
        if sensor.get_value("button_1") == 1:
            print('Recording will start in 3 seconds')
            on_hold = False
            time.sleep(3)
        time.sleep(.02)
        if not on_hold:
            print('Starting recording...')
            start_time = time.time()
            last_recorded_time = start_time

    # Get current time once at the beginning
    curr_time = time.time()

    # Get interval between current and last execution
    interval = curr_time - last_recorded_time

    # Update last recorded time for next execution
    last_recorded_time = curr_time

    # Get sensor data and format for csv...
    gyro_data = sensor.get_value("gyroscope")
    acc_data = sensor.get_value("accelerometer")
    ax, ay, az = acc_data['x'], acc_data['y'], acc_data['z']
    gx, gy, gz = gyro_data['x'], gyro_data['y'], gyro_data['z']
    # ...and add it to the existing csv
    csv += f'{str(data_id)},{curr_time},{ax},{ay},{az},{gx},{gy},{gz}\n'

    # Add interval to run time
    run_time += interval

    # Add 1 to id
    data_id += 1

    # Assuming that this sampling is good enough for our use case
    time.sleep(pause_time)

print("Recording finished")
sensor.disconnect()
# Define path and save data
path = os.path.join('data', filename)
with open(path, 'w') as f:
    f.write(csv)
    sys.exit()

