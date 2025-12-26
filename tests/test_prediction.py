
import os
import random
import sys
import time

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.prediction import PredictionSystem


class MockConfig:
    def __init__(self):
        self.smoothing = 5.0
        self.prediction_multiplier = 1.0
        self.prediction_enabled = True

def test_prediction_stability():
    config = MockConfig()
    pred = PredictionSystem(config)

    print("Testing One Euro Filter Prediction System...")

    # Test 1: Stability (Jitter Reduction)
    # Target is STATIONARY (100, 100) but detection adds NOISE (+/- 5px)
    print("\n[Test 1] Jitter Reduction (Stationary Target with Noise)")
    center_x = 100
    for i in range(10):
        # Time step
        dt = 0.016
        time.sleep(dt)

        noise = random.randint(-5, 5)
        raw_x = center_x + noise

        px, py = pred.predict(raw_x, 100)

        # With smoothing=5.0, the prediction should be much closer to 100 than the raw noise
        print(f"Frame {i}: Raw={raw_x}, Pred={px}, Noise={noise}, Error={px-center_x}")

    # Test 2: Responsiveness (High Speed)
    # Target MOVES FAST. Filter should lower cutoff to reduce lag.
    print("\n[Test 2] High Speed Responsiveness")
    # Reset filter state effectively by jumping
    start_x = 100
    velocity = 100 # pixels per frame (very fast)

    for i in range(10):
        dt = 0.016
        time.sleep(dt)

        target_x = start_x + velocity * (i+1)
        px, py = pred.predict(target_x, 100)

        # Prediction should lead the target due to velocity
        lag = target_x - px
        print(f"Frame {i}: Target={target_x}, Pred={px}, Lag={lag} (Negative means leading)")

    print("Test Complete.")

if __name__ == "__main__":
    test_prediction_stability()
