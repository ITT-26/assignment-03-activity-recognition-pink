import glob, os
import numpy as np
import pandas as pd
from collections import deque
from sklearn import svm
from sklearn.preprocessing import StandardScaler
from DIPPID import SensorUDP

PORT = 5700
SAMPLING_RATE = 20
WIN = 51   # 2.56s at 20Hz
STEP = 25  # 50% overlap
TRIM = 25
COLS = ['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z']


def _extract_features(w):
    freqs = np.fft.rfftfreq(WIN, d=1/SAMPLING_RATE)
    fft_mag = np.abs(np.fft.rfft(w, axis=1))
    dominant_freq = freqs[fft_mag[:, 1:].argmax(axis=1) + 1]
    return np.array([
        *w.mean(1), *w.std(1), *np.ptp(w, axis=1),
        *[(np.diff(np.sign(r)) != 0).sum() / len(r) for r in w],
        *np.sqrt((w[3:]**2).mean(1)),
        *dominant_freq
    ])


def _load_and_train(placement):
    print(f'Training model for placement={placement}...')

    dfs = []
    for path in glob.glob('shared_data/**/*.csv', recursive=True):
        parts = os.path.basename(path).replace('.csv', '').split('-')
        df = pd.read_csv(path)
        df['person'], df['activity'], df['frequency'], df['placement'], df['trial'] = \
            parts[0], parts[1], parts[2], parts[3], int(parts[4])
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)

    for col in ['person', 'activity', 'placement']:
        df[col] = df[col].str.lower()
    df = df[df['person'] != 'susi']
    df = df[df['person'] != 'felix']

    df.loc[df['person'].isin(['lennart', 'maximilian']), ['gyro_x', 'gyro_y', 'gyro_z']] /= (180 / np.pi)

    rows, labels = [], []
    subset = df[(df['frequency'] == '20Hz') & (df['placement'] == placement)]
    for (_, activity, _, trial), g in subset.groupby(['person', 'activity', 'placement', 'trial']):
        g = g.reset_index(drop=True)
        for s in range(TRIM, len(g) - WIN + 1, STEP):
            w = g.iloc[s:s + WIN][COLS].values.T
            rows.append(_extract_features(w))
            labels.append(activity)

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
        self.clf, self.scaler = _load_and_train(placement)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def tick(self, dt):
        if not self.sensor.has_capability('accelerometer'):
            print('DIPPID device not found')
            return

        acc  = self.sensor.get_value('accelerometer')
        gyro = self.sensor.get_value('gyroscope')
        self.buffer.append([acc['x'], acc['y'], acc['z'],
                            gyro['x'], gyro['y'], gyro['z']])
        self.samples_since_predict += 1

        if len(self.buffer) == WIN and self.samples_since_predict >= STEP:
            w = np.array(self.buffer).T
            if w[:3].std() < 0.3:  # acc channels near-zero variance = idle
                self.current_activity = None
            else:
                features = self.scaler.transform([_extract_features(w)])
                self.current_activity = self.clf.predict(features)[0]
            self.samples_since_predict = 0
