import sys

sys.path.insert(0, ".")
from core.motion_engine import MotionEngine


class MockConfig:
    def __init__(self, prediction_scale=1.0):
        self.motion_min_cutoff = 0.5
        self.motion_beta = 0.005
        self.prediction_scale = prediction_scale
        self.screen_width = 1920
        self.screen_height = 1080


def run_analysis(scale):
    config = MockConfig(scale)
    engine = MotionEngine(config)
    dt = 0.016

    # 1. Constant Velocity Phase (to measure steady-state lead/lag)
    vx = 500  # Fast movement
    x = 0
    t = 0

    steady_state_errors = []
    for i in range(100):
        x += vx * dt
        out_x, _ = engine.process(x, 540, dt)
        if i > 50:  # Wait for filter to stabilize
            steady_state_errors.append(out_x - x)
        t += dt

    avg_ss_error = sum(steady_state_errors) / len(steady_state_errors)

    # 2. Sudden Stop Phase (to measure overshoot)
    overshoot_errors = []
    # x is currently at some value, now it stops moving
    for _ in range(30):
        # x stays same
        out_x, _ = engine.process(x, 540, dt)
        overshoot_errors.append(out_x - x)
        t += dt

    max_overshoot = max(overshoot_errors) if vx > 0 else min(overshoot_errors)

    # 3. Direction Reversal (to measure "weirdness" during turn)
    vx_rev = -500
    reversal_errors = []
    for _ in range(50):
        x += vx_rev * dt
        out_x, _ = engine.process(x, 540, dt)
        reversal_errors.append(out_x - x)
        t += dt

    max_reversal_error = max([abs(e) for e in reversal_errors])

    return {
        "scale": scale,
        "ss_error": avg_ss_error,
        "max_overshoot": max_overshoot,
        "max_rev_error": max_reversal_error,
    }


if __name__ == "__main__":
    print(f"{'Scale':<10} | {'Steady State Error':<20} | {'Max Overshoot':<15} | {'Max Reversal Error':<20}")
    print("-" * 75)
    for s in [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]:
        res = run_analysis(s)
        print(
            f"{res['scale']:<10.1f} | {res['ss_error']:<20.1f} | {res['max_overshoot']:<15.1f} | {res['max_rev_error']:<20.1f}"
        )

    print("\nInterpretation:")
    print("- Positive SS Error: Leading the target (Predicting ahead)")
    print("- Negative SS Error: Lagging the target (Smoothing lag > Prediction)")
    print("- Max Overshoot: Distance traveled AFTER target stopped")
    print("- Max Reversal Error: Worst case error during 180-degree turn")
