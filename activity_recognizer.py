import glob, os
import numpy as np
import pandas as pd
from collections import deque
from sklearn import svm
from sklearn.preprocessing import StandardScaler
from DIPPID import SensorUDP

IS_M5_STACK = False

PORT = 5700
SAMPLING_RATE = 20
SAMPLE_INTERVAL = 1.0 / SAMPLING_RATE
WIN = 51   # 2.56s at 20Hz
STEP = 25  # 50% overlap
TRIM = 0
COLS = ['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z']


def _extract_features(w):
    freqs = np.fft.rfftfreq(WIN, d=1/SAMPLING_RATE)
    fft_mag = np.abs(np.fft.rfft(w, axis=1))
    dominant_freq = freqs[fft_mag[:, 1:].argmax(axis=1) + 1]
    return np.array([
        *w.mean(1),
        *w.std(1),
        *np.ptp(w, axis=1),  # Peak-to-peak (max - min)
        *[(np.diff(np.sign(r)) != 0).sum() / len(r) for r in w],  # Zero-crossing rate
        *np.sqrt((w[3:]**2).mean(1)),  # Root mean square (RMS) energy
        *dominant_freq
    ])

def _load_and_train(placement):
    print(f'Training model for placement={placement}...')
    rows, labels = [], []
    for path in glob.glob('shared_data/**/*.csv', recursive=True):
        parts = os.path.basename(path).replace('.csv', '').split('-')
        person, activity, frequency, file_placement = (p.lower() for p in parts[:4])
        if person in ('susi', 'felix'):
            continue
        if frequency != '20hz':
            continue
        if file_placement != placement:
            continue
        df = pd.read_csv(path)
        if person in ('lennart', 'maximilian'):
            df[['gyro_x', 'gyro_y', 'gyro_z']] /= (180 / np.pi)
        arr = df[COLS].to_numpy()
        for s in range(TRIM, len(arr) - WIN + 1, STEP):
            w = arr[s:s + WIN].T
            rows.append(_extract_features(w))
            labels.append(activity)
        del df, arr
    X = np.array(rows)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    clf = svm.SVC(kernel='linear')
    clf.fit(X, labels)
    print('Training done.')
    return clf, scaler


class ActivityRecognizer:
    def __init__(self, placement='hand'):
        self.sensor = SensorUDP(PORT)
        self.buffer = deque(maxlen=WIN)
        self.samples_since_predict = 0
        self.current_activity = None
        self._sample_accum = 0.0
        self.clf, self.scaler = _load_and_train(placement)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def tick(self, dt):
        self._sample_accum += dt
        if self._sample_accum < SAMPLE_INTERVAL:
            return
        self._sample_accum -= SAMPLE_INTERVAL
        if not self.sensor.has_capability('accelerometer'):
            print('DIPPID device not found')
            return
        acc  = self.sensor.get_value('accelerometer')
        gyro = self.sensor.get_value('gyroscope')
        gyro_scale = np.pi / 180 if IS_M5_STACK else 1.0  # Convert degrees/s to radians/s for M5Stack data
        self.buffer.append([
            acc['x'], acc['y'], acc['z'],
            gyro['x'] * gyro_scale,
            gyro['y'] * gyro_scale,
            gyro['z'] * gyro_scale,
        ])

        self.samples_since_predict += 1
        if len(self.buffer) == WIN and self.samples_since_predict >= STEP:
            w = np.array(self.buffer).T
            if w[:3].std() < 0.3:
                self.current_activity = None
            else:
                features = self.scaler.transform([_extract_features(w)])
                self.current_activity = self.clf.predict(features)[0]
            self.samples_since_predict = 0
