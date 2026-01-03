
import pytest

from core.motion_engine import MotionEngine


class MockConfig:
    def __init__(self):
        self.motion_min_cutoff = 0.5
        self.motion_beta = 0.005
        self.prediction_scale = 2.0  # Strong prediction
        self.screen_width = 1920.0
        self.screen_height = 1080.0

@pytest.fixture
def motion_engine():
    config = MockConfig()
    return MotionEngine(config)

def test_vertical_prediction_bug(motion_engine):
    """
    Demonstrates that vertical-only movement fails to trigger prediction
    due to reliance on abs(dx) for the velocity gate.
    """
    # 1. Initialize
    motion_engine.process(100, 0, 0.016)

    # 2. Move Vertically ONLY (0 -> 100 in Y)
    # We simulate a jump or fast movement.
    # To get high velocity, we need a large change in short time.
    # But 1Euro filter smooths it.

    # Let's feed a sequence of vertical movements.
    y = 0
    dt = 0.016

    # Ramp up speed
    for _ in range(10):
        y += 10 # 10 px per frame -> 10/0.016 = 625 px/sec
        motion_engine.process(100, y, dt)

    # Now we are moving fast vertically.
    # dx should be 0 (x stayed at 100).
    # dy should be ~625.

    assert abs(motion_engine.x_filter.deriv_prev) < 1.0
    assert abs(motion_engine.y_filter.deriv_prev) > 100.0

    # Now check prediction
    # If the bug exists, vel_scale relies on abs(dx) which is ~0.
    # So vel_scale ~ 0.
    # So lookahead ~ 0.
    # So pred_y ~ smoothed_y.

    # Let's peek at the next process call result compared to raw smoothing
    next_y = y + 10

    # We need to access internal state to see "smoothed_y" vs "returned y"
    # But we can just check if the returned value is significantly ahead of the input?
    # No, smoothed value lags. Predicted value attempts to catch up.

    # Let's capture the state
    dy = motion_engine.y_filter.deriv_prev

    # Calculate what prediction SHOULD be
    # vel_scale should be 1.0 (speed > 100)
    # lookahead = 0.1 * 2.0 * 1.0 = 0.2
    # pred_y = smoothed_y + dy * 0.2

    # Let's run one more frame
    _, res_y = motion_engine.process(100, next_y, dt)

    smoothed_y_after = motion_engine.y_filter.value_prev
    # dy is roughly same

    # If bug exists, res_y will be close to smoothed_y_after
    # If fixed, res_y will be smoothed_y_after + (dy * 0.2)

    diff = res_y - smoothed_y_after
    expected_boost = dy * 0.2

    print(f"DY: {dy}, Diff: {diff}, Expected Boost: {expected_boost}")

    # With the bug, diff is approx 0.
    # We assert that diff is significant (e.g. > 25% of expected)
    # NOTE: Threshold lowered from 50% to 25% to account for adaptive damping
    # and clamping logic added in V3.4.2 to prevent overshooting.
    # The key assertion is that diff >> 0 (vertical prediction IS triggering).
    assert diff > (expected_boost * 0.25), "Vertical prediction failed to trigger!"
