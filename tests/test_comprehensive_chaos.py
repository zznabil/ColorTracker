"""
Comprehensive Chaos Monkey Test Suite

ULTRATHINK Protocol: Combine concurrent config hammering, temporal jitter,
and multi-monitor coordinate simulation to stress cross-module stability.
"""

import random
import threading
import time
from unittest.mock import patch

import numpy as np
import pytest

from core.detection import DetectionSystem
from core.low_level_movement import LowLevelMovementSystem
from core.prediction import PredictionSystem
from utils.config import Config
from utils.logger import Logger


class TestComprehensiveChaos:
    def test_integrated_stress_loop(self):
        """
        Integrated stress test:
        1. Thread A: Rapid config updates (simulating UI/Settings hammering).
        2. Thread B: Rapid detection-prediction-movement cycles with jittered timing.
        3. Thread C: Logger spam.
        """
        config = Config()
        config.fov_x = 100
        config.fov_y = 100

        # System mocks
        ds = DetectionSystem(config)
        ps = PredictionSystem(config)
        with patch("ctypes.windll.user32.GetSystemMetrics", return_value=1920):  # Mock for init
            ms = LowLevelMovementSystem(config)

        stop_event = threading.Event()
        errors = []

        def config_hammer():
            try:
                while not stop_event.is_set():
                    config.update("prediction_multiplier", random.uniform(0.1, 5.0))
                    config.update("smoothing", random.uniform(0.0, 100.0))
                    config.update("fov_x", random.randint(10, 500))
                    time.sleep(0.01)
            except Exception as e:
                errors.append(f"Config hammer error: {e}")

        def logic_loop():
            try:
                base_time = time.time()
                for i in range(500):
                    if stop_event.is_set():
                        break

                    # Simulate time jitter (1-32ms steps)
                    jittered_time = base_time + (i * 0.016) + random.uniform(-0.005, 0.005)

                    # Mock SCT for detection
                    with patch.object(ds, "_get_sct") as mock_sct:
                        img = np.zeros((config.fov_y, config.fov_x, 4), dtype=np.uint8)
                        # Target moving in circle
                        tx = (config.fov_x // 2) + int(20 * np.cos(i * 0.1))
                        ty = (config.fov_y // 2) + int(20 * np.sin(i * 0.1))
                        # Bound checks
                        tx = max(0, min(config.fov_x - 1, tx))
                        ty = max(0, min(config.fov_y - 1, ty))
                        img[ty, tx] = [0, 0, 255, 255]
                        mock_sct.return_value.grab.return_value = img

                        found, dx, dy = ds.find_target()

                        if found:
                            with patch("time.time", return_value=jittered_time):
                                px, py = ps.predict(dx, dy)

                                # Move mouse (mocked)
                                with patch("ctypes.windll.user32.SendInput", return_value=1):
                                    ms.move_to_target(px, py)

            except Exception as e:
                errors.append(f"Logic loop error: {e}")

        def logger_stress():
            logger = Logger()
            try:
                while not stop_event.is_set():
                    logger.debug(f"Chaos noise {random.random()}")
                    time.sleep(0.005)
            except Exception as e:
                errors.append(f"Logger stress error: {e}")

        t_conf = threading.Thread(target=config_hammer)
        t_logic = threading.Thread(target=logic_loop)
        t_log = threading.Thread(target=logger_stress)

        t_conf.start()
        t_logic.start()
        t_log.start()

        t_logic.join()
        stop_event.set()
        t_conf.join()
        t_log.join()

        assert not errors, f"Stress test failed with errors: {errors}"

    def test_extreme_coordinate_traversal(self):
        """Test movement mathematics with extreme multi-monitor coordinates"""
        config = Config()
        all_metrics = [[1920, 1080], [3840, 2160], [7680, 4320]]  # FHD, 4K, 8K

        for w, h in all_metrics:
            with patch("ctypes.windll.user32.GetSystemMetrics", side_effect=[w, h]):
                ms = LowLevelMovementSystem(config)

                # Far edges
                test_points = [
                    (0, 0),
                    (w, h),
                    (-1000, -1000),
                    (w + 1000, h + 1000),
                    (random.uniform(-1e6, 1e6), random.uniform(-1e6, 1e6)),
                ]

                for x, y in test_points:
                    with patch("ctypes.windll.user32.SendInput", return_value=1) as mock_send:
                        ms.move_mouse_absolute(x, y)
                        assert mock_send.called
                        # Verify the structure of SendInput call if possible,
                        # but at minimum ensure no overflow exception in Python


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
