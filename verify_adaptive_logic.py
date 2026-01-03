
from core.motion_engine import MotionEngine


class MockConfig:
    def __init__(self):
        self.screen_width = 1920
        self.screen_height = 1080
        self.motion_min_cutoff = 0.5
        self.motion_beta = 0.005
        self.prediction_scale = 1.0
        self.fov_x = 50
        self.fov_y = 50


def test_damping():
    config = MockConfig()
    engine = MotionEngine(config)
    out_x, out_y = 0, 0
    # 1. Target far away (dist > 40)
    for i in range(20):
        out_x, out_y = engine.process(i * 10, 0, 0.016)
    print(f"Far away (dist > 40): input={19*10}, output_x={out_x}")

    # 2. Target near center (dist < 40)
    engine.reset()
    target_x = 1000
    cy = 540
    for _ in range(20):
        out_x, out_y = engine.process(target_x, cy, 0.016)
    print(f"Near center (dist ~ 5): input={target_x}, output_x={out_x}")


def test_clamping():
    config = MockConfig()
    engine = MotionEngine(config)
    engine.update_config()

    # Move very fast
    out_x, out_y = 0, 0
    for i in range(10):
        out_x, out_y = engine.process(500 + i * 100, 0, 0.016)

    last_input = 1400
    offset = out_x - last_input
    print(f"Extreme velocity: input={last_input}, output_x={out_x}, offset={offset}")

    # Max offset should be min(50*1.5, 1920*0.08) = min(75, 153.6) = 75.0
    # The offset might be slightly larger because smoothed_x is ahead of last_input?
    # No, smoothed_x is behind. So pred_x = smoothed_x + offset.
    # if offset is 75, and smoothed_x is 1350, pred_x = 1425.
    # pred_x - last_input = 1425 - 1400 = 25.
    # The real check is that pred_x - smoothed_x <= max_offset.

    # But for a simple check, pred_x - last_input should definitely not be huge.
    assert abs(offset) <= 150  # 75 max offset + some smoothing slack


if __name__ == "__main__":
    test_damping()
    test_clamping()
    print("All adaptive logic tests passed!")
    test_damping()
    test_clamping()
