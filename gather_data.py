import os
import time
import pandas as pd
from DIPPID import SensorUDP

DURATION = 10  # seconds per recording
ACTIVITIES = ["running", "rowing", "lifting", "jumpingjacks"]
SAMPLING_RATES = [20, 100]
PLACEMENTS = ["hand", "pocket"]
combos = [(a, p, r, n) for p in PLACEMENTS for a in ACTIVITIES for r in SAMPLING_RATES for n in range(1, 6)]  # 5 recordings per combo

PORT = 5700
sensor = SensorUDP(PORT)

name = input("Enter name: ")
os.makedirs("data", exist_ok=True)

try:
    for activity, placement, sampling_rate, recording_num in combos:
        print(f"Get ready for {activity} at {sampling_rate}Hz with sensor on {placement} for {DURATION} seconds, recording #{recording_num}.")
        print("Press button 1 on your DIPPID device to start recording. You will have 2 seconds after pressing to get into position.")

        while True:
            if sensor.has_capability("button_1"):
                if int(sensor.get_value("button_1")) == 1:
                    break
            time.sleep(0.005)  # check every 5ms

        print("Starting in 2 seconds....")
        time.sleep(1)
        print("Starting in 1 second...")
        time.sleep(1)

        rows = []
        id = 0
        start_time = time.time()
        interval = 1 / sampling_rate
        print("Recording...")
        while time.time() - start_time < DURATION:
            acc_data = sensor.get_value("accelerometer")
            gyro_data = sensor.get_value("gyroscope")
            rows.append({
                "id": id,
                "timestamp": int(time.time() * 1000),
                "acc_x": acc_data['x'], "acc_y": acc_data['y'], "acc_z": acc_data['z'],
                "gyro_x": gyro_data['x'], "gyro_y": gyro_data['y'], "gyro_z": gyro_data['z'],
            })
            id += 1
            time.sleep(max(0, start_time + id * interval - time.time()))  # maintain consistent sampling rate
        
        df = pd.DataFrame(rows)
        filename = os.path.join("data", f"{name}-{activity}-{sampling_rate}Hz-{placement}-{recording_num}.csv")
        df.to_csv(filename, index=False)
        print(f"Saved {filename}\n")
    print("All recordings complete!")
except KeyboardInterrupt:
    print("Recording interrupted. Exiting...")
finally:    
    os._exit(0)