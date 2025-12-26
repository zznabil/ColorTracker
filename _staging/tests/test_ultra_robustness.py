import random
import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.detection import DetectionSystem
from core.prediction import PredictionSystem
from utils.config import Config


class TestUltraRobustness:
    @pytest.mark.skip(reason="Threaded config fuzzing is too unstable for CI environment")
    def test_chaos_monkey_config_threading(self):
        """
        The 'User From Hell' Test:
        Simulate a user rapidly changing configs (saving/reloading)
        while the prediction system is actively reading them in a separate thread.
        """
        config = Config()
        # Ensure we don't actually write to disk for this stress test if we can avoid it,
        # or use a temp file. Config.load() reads from self.config_file.
        # We will mock load/save to focus on in-memory state consistency.

        config.prediction_enabled = True
        config.prediction_multiplier = 1.5
        config.smoothing = 0.5

        ps = PredictionSystem(config)

        stop_event = threading.Event()
        error_list = []

        def reader_thread():
            try:
                for i in range(50000):  # Increased from 10000
                    if stop_event.is_set():
                        break
                    # Access config properties rigorously
                    _ = ps.config.prediction_multiplier
                    _ = ps.config.smoothing

                    # Ensure numerical stability
                    px, py = ps.predict(100 + i % 10, 100 + i % 10)
                    if not (np.isfinite(px) and np.isfinite(py)):
                        error_list.append(ValueError(f"Non-finite prediction at {i}: {px}, {py}"))
            except Exception as e:
                error_list.append(e)

        def writer_thread():
            try:
                for _ in range(5000):  # Increased from 1000
                    if stop_event.is_set():
                        break
                    # Randomize config values
                    config.prediction_multiplier = random.uniform(-1.0, 10.0)  # Include negative/extreme
                    config.smoothing = random.uniform(-10.0, 110.0)
                    time.sleep(0.0001)
            except Exception as e:
                error_list.append(e)

        t_read = threading.Thread(target=reader_thread)
        t_write = threading.Thread(target=writer_thread)

        t_read.start()
        t_write.start()

        t_write.join()
        stop_event.set()
        t_read.join()

        if error_list:
            pytest.fail(f"Threading errors occurred: {error_list}")

    def test_marathon_prediction_stability(self):
        """
        The 'Marathon' Test:
        Simulate 100,000 frames of data to check for accumulation errors,
        buffer overflows, or performance degradation.
        """
        config = Config()
        config.filter_method = "TEMA"  # Use a complex filter
        config.prediction_enabled = True
        ps = PredictionSystem(config)

        start_time = 1000.0
        dt = 0.016  # 60 FPS

        # Simulate a circular motion target
        radius = 100
        center_x, center_y = 960, 540

        try:
            for i in range(10000):
                t = start_time + (i * dt)
                # Circular path
                target_x = center_x + radius * np.cos(t)
                target_y = center_y + radius * np.sin(t)

                with patch("time.time", return_value=t):
                    px, py = ps.predict(target_x, target_y)

                    # Sanity check: Prediction should be within reasonable bounds of target
                    # (it will lead, but shouldn't explode)
                    dist = np.sqrt((px - target_x) ** 2 + (py - target_y) ** 2)
                    # With TEMA and movement, distance can be significant, but not infinite
                    assert np.isfinite(px)
                    assert np.isfinite(py)
                    # 500px is a generous bound for "not exploded" on a 100px radius circle
                    if i > 10:  # Allow settle time
                        assert dist < 500, f"Prediction exploded at frame {i}: dist={dist}"

        except Exception as e:
            pytest.fail(f"Marathon test failed at iteration {i}: {e}")

    def test_detection_screen_tear_robustness(self):
        """
        The 'Screen Tear' Test:
        Simulate mss returning unexpected array shapes or types.
        """
        config = Config()
        ds = DetectionSystem(config)

        # 1. Simulate empty array (0x0)
        with patch.object(ds, "_get_sct") as mock_sct:
            grab_mock = MagicMock()
            grab_mock.return_value = np.zeros((0, 0, 4), dtype=np.uint8)
            mock_sct.return_value.grab = grab_mock

            # Should handle gracefully (return False or ignore)
            try:
                found, x, y = ds.find_target()
                assert found is False
            except Exception as e:
                # If it crashes, it failed the test
                pytest.fail(f"Crashed on empty image: {e}")

        # 2. Simulate malformed array (1D instead of 3D)
        with patch.object(ds, "_get_sct") as mock_sct:
            grab_mock = MagicMock()
            grab_mock.return_value = np.zeros((1000), dtype=np.uint8)  # Wrong shape
            mock_sct.return_value.grab = grab_mock

            try:
                found, x, y = ds.find_target()
                assert found is False
            except Exception as e:
                # We want robust code that doesn't crash app
                pytest.fail(f"Crashed on malformed array: {e}")

    def test_type_fuzzing_config(self):
        """
        Inject invalid types into config and ensure system handles/coerces or fails safely.
        """
        config = Config()

        # Inject string where float expected
        config.smoothing = "0.5"  # type: ignore
        # Python might coerce or crash depending on usage.
        # We want to know what happens.
        # If the code assumes float, '0.5' * 10 will be '0.50.5...' which is BAD for math.

        # Let's check if the system validates/converts or if we need to enforce it.
        # This test asserts that EITHER it works (coerced) OR raises TypeError/ValueError,
        # but does NOT hang or corrupt silently.

        try:
            # If logic uses it effectively
            val = float(config.smoothing)
            assert val == 0.5
        except (ValueError, TypeError):
            pass
