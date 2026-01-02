#!/usr/bin/env python3
"""
Simulation to investigate motion engine prediction behavior with varying prediction_scale.
"""

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


def simulate_linear_motion(
    prediction_scale, duration=1.0, dt=0.016, start_x=0, start_y=0, velocity_x=100, velocity_y=0
):
    """Simulate a target moving at constant velocity and record engine output."""
    config = MockConfig(prediction_scale)
    engine = MotionEngine(config)

    results = []
    t = 0.0
    x = start_x
    y = start_y

    # First frame to initialize
    out_x, out_y = engine.process(x, y, dt)
    results.append((t, x, y, out_x, out_y, 0, 0))

    steps = int(duration / dt)
    for _ in range(1, steps):
        t += dt
        x = start_x + velocity_x * t
        y = start_y + velocity_y * t
        out_x, out_y = engine.process(x, y, dt)
        error_x = out_x - x
        error_y = out_y - y
        results.append((t, x, y, out_x, out_y, error_x, error_y))

    return results


def analyze_results(results):
    """Compute statistics about the error."""
    errors_x = [r[5] for r in results]
    errors_y = [r[6] for r in results]
    max_abs_error_x = max([abs(e) for e in errors_x])
    max_abs_error_y = max([abs(e) for e in errors_y])
    avg_error_x = sum(errors_x) / len(errors_x)
    avg_error_y = sum(errors_y) / len(errors_y)
    return max_abs_error_x, max_abs_error_y, avg_error_x, avg_error_y


if __name__ == "__main__":
    print("Prediction Scale Comparison")
    print("=" * 60)
    scales = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0]
    for scale in scales:
        results = simulate_linear_motion(scale, duration=0.5, dt=0.016, velocity_x=200, velocity_y=0)
        max_x, max_y, avg_x, avg_y = analyze_results(results)
        print(f"Scale {scale:4.1f}: Max Error X={max_x:6.1f}, Avg Error X={avg_x:6.1f}")

    # Also test with slow movement
    print("\nSlow movement (velocity 50 px/sec):")
    for scale in scales:
        results = simulate_linear_motion(scale, duration=0.5, dt=0.016, velocity_x=50, velocity_y=0)
        max_x, max_y, avg_x, avg_y = analyze_results(results)
        print(f"Scale {scale:4.1f}: Max Error X={max_x:6.1f}, Avg Error X={avg_x:6.1f}")

    # Test with oscillating target (change direction)
    print("\nOscillating target (velocity changes sign):")

    # Simulate target moving back and forth
    def simulate_oscillation(scale):
        config = MockConfig(scale)
        engine = MotionEngine(config)
        dt = 0.016
        t = 0.0
        x = 0
        results = []
        for i in range(50):
            # Alternate direction every 10 frames
            if i < 10:
                vx = 100
            elif i < 20:
                vx = -100
            else:
                vx = 100
            x += vx * dt
            out_x, out_y = engine.process(x, 0, dt)
            error = out_x - x
            results.append((t, x, out_x, error))
            t += dt
        return results

    for scale in [0.0, 1.0, 5.0, 10.0]:
        res = simulate_oscillation(scale)
        errors = [r[3] for r in res]
        max_abs = max([abs(e) for e in errors])
        avg = sum(errors) / len(errors)
        print(f"Scale {scale:4.1f}: Max Abs Error={max_abs:6.1f}, Avg Error={avg:6.1f}")
