import csv
import time
import sys
from DIPPID import SensorUDP


ACTIVITIES = ["running", "rowing", "lifting", "jumpingjacks"]
SAMPLING_RATES = [20, 100]
PLACEMENTS = ["hand", "pocket"]
DURATION = 10  # seconds per recording

PORT = 5700
sensor = SensorUDP(PORT)

while(True):
    # print all capabilities of the sensor
    print('capabilities: ', sensor.get_capabilities())

    # check if the sensor has the 'accelerometer' capability
    if(sensor.has_capability('accelerometer')):
        # print whole accelerometer object (dictionary)
        print('accelerometer data: ', sensor.get_value('accelerometer'))

        # print only one accelerometer axis
        print('accelerometer X: ', sensor.get_value('accelerometer')['x'])

    # if sensor.has_capability('button_1'):
    #     print('button_1: ', sensor.get_value('button_1'))

    time.sleep(1)
