import time
from unittest.mock import MagicMock, patch

import numpy as np

from core.detection import DetectionSystem
from core.low_level_movement import LowLevelMovementSystem
from core.motion_engine import MotionEngine


class MockConfig:
    def __init__(self):
        self.screen_width = 1920
        self.screen_height = 1080
        self.fov_x = 100
        self.fov_y = 100
        self.target_color = 0xC9008D
        self.color_tolerance = 10
        self.mouse_smoothing = 0.5
        self.prediction_factor = 1.0
        self.ultra_responsive_mode = False
        self.zero_latency_mode = False

def test_full_pipeline_throughput():
    """Stress test the full loop: Detection -> Prediction -> Movement"""
    config = MockConfig()

    # Mocking SCT to return a fake image quickly
    with patch("mss.mss") as mock_mss:
        sct_instance = mock_mss.return_value
        # Create a dummy image (100x100 BGR)
        dummy_img = np.zeros((200, 200, 4), dtype=np.uint8)
        # Put the target color in it at some position
        # target_color 0xC9008D -> R=C9, G=00, B=8D -> BGR: 8D, 00, C9
        dummy_img[50, 50] = [0x8D, 0x00, 0xC9, 255]
        sct_instance.grab.return_value = dummy_img

        # Initialize systems
        ds = DetectionSystem(config, MagicMock())
        me = MotionEngine(config)
        ms = LowLevelMovementSystem(config, MagicMock())

        # Bypass SendInput to avoid actual movement during test
        with patch("ctypes.windll.user32.SendInput", return_value=1):
            start_time = time.time()
            iterations = 500

            for _ in range(iterations):
                # 1. Detect
                found, tx, ty = ds.find_target()

                # 2. Predict if found
                if found:
                    px, py = me.process(tx, ty, 0.0)

                    # 3. Move
                    ms.aim_at(px, py)

                # Small jitter to simulate movement in consecutive frames
                # In next iteration, we'd ideally update dummy_img to move the pixel
                # but for throughput test, static is fine.

            end_time = time.time()
            total_time = end_time - start_time
            avg_ms = (total_time / iterations) * 1000

            print(f"\nThroughput results: {iterations} iterations in {total_time:.2f}s")
            print(f"Average latency per loop: {avg_ms:.2f}ms")

            # Assert that the loop is reasonably fast (< 10ms per iteration on decent hardware)
            # In CI environments this might be slower, so we use a generous threshold.
            assert avg_ms < 50.0


def test_prediction_drift_under_oscillation():
    """Verify prediction stability when target oscillates rapidly"""
    config = MockConfig()
    ps = MotionEngine(config)

    # Oscillate between two points
    points = [(100, 100), (200, 200)] * 50
    dt = 0.016  # 60 FPS

    current_time = 100.0
    for x, y in points:
        with patch("time.time", return_value=current_time):
            # Using 0.0 as dt to rely on internal time or just mock if needed
            # Since motion_engine uses perfor_counter directly, we might need to patch perf_counter
            with patch("time.perf_counter", return_value=current_time):
                px, py = ps.process(x, y, 0.0)
            assert np.isfinite(px) and np.isfinite(py)
        current_time += dt
