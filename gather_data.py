import time
import pandas as pd
from DIPPID import SensorUDP

DURATION = 10  # seconds per recording

ACTIVITIES = ["running", "rowing", "lifting", "jumpingjacks"]
SAMPLING_RATES = [20, 100]
PLACEMENTS = ["hand", "pocket"]
combos = [(a, r, p) for a in ACTIVITIES for r in SAMPLING_RATES for p in PLACEMENTS]

PORT = 5700
sensor = SensorUDP(PORT)

name = input("Enter name: ")

for activity, sampling_rate, placement in combos:
    print(f"Get ready for  {activity} at {sampling_rate}Hz with sensor on {placement} for {DURATION} seconds.")
    print("Press button 1 to start recording...")

    with True:
        if sensor.has_capability("button_1"):
            if int(sensor.get_value("button_1")) == 1:
                break
        time.sleep(0.02)  # check every 20ms

    df = pd.DataFrame(columns=["id", "timestamp", "acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"])
    
    time.sleep(2)  # small delay before starting to record
    print("Recording...")
    id = 0
    start_time = time.time()
    while time.time() - start_time < DURATION:
        timestamp = time.time()
        acc_data = sensor.get_value("accelerometer")
        gyro_data = sensor.get_value("gyroscope")
        df = df.append({    "id": id,
                            "timestamp": timestamp,
                            "acc_x": acc_data['x'],
                            "acc_y": acc_data['y'],
                            "acc_z": acc_data['z'],
                            "gyro_x": gyro_data['x'],
                            "gyro_y": gyro_data['y'],
                            "gyro_z": gyro_data['z']
                        }, ignore_index=True)
        id += 1
        time.sleep(1/sampling_rate)

    filename = f"{name}_{activity}_{sampling_rate}Hz_{placement}.csv"
    df.to_csv(filename, index=False)
    print(f"Saved {filename}\n")