import time
from activity_recognizer import ActivityRecognizer, SAMPLING_RATE

with ActivityRecognizer(placement='hand') as recognizer:
    while True:
        recognizer.tick(0)
        print(f'buffer={len(recognizer.buffer)}, activity={recognizer.current_activity}')
        time.sleep(1 / SAMPLING_RATE)
