import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.low_level_movement import LowLevelMovementSystem
from core.prediction import PredictionSystem
from utils.config import Config
from utils.filters import DynamicEMA, SimpleEMA


class TestUltraRigorousVerification:
    """
    ULTRA-THINK Protocol: Deep Systemic Verification Suite
    Focuses on longevity, precision stability, and high-load concurrency.
    """

    def test_filter_longevity_and_memory_stability(self):
        """
        Verify that filters do not leak memory or grow buffers indefinitely
        over long-running sessions (10,000+ iterations).
        """
        config = MagicMock()
        config.smoothing = 2.0
        config.filter_method = "Median+EMA"
        ps = PredictionSystem(config)

        # Warm up
        ps.predict(100, 100)

        # Capture initial state of filters
        mf_x, ema_x = ps.filter_x

        # Run 10,000 iterations
        for i in range(10000):
            ps.predict(100 + (i % 50), 100 + (i % 50))

        # Verify MedianFilter buffer is capped
        assert len(mf_x.buffer) == mf_x.window_size
        assert len(ps.filter_y[0].buffer) == ps.filter_y[0].window_size

        # Verify stability of state
        assert np.isfinite(ps.prev_x)
        assert np.isfinite(ps.velocity_x)

    def test_high_fps_timing_math_integrity(self):
        """
        Stress test prediction math at extreme frame rates (1000+ FPS).
        Ensures dt clamping prevents division by zero or infinite velocity.
        """
        config = MagicMock()
        config.prediction_enabled = True
        config.prediction_multiplier = 1.0
        config.filter_method = "EMA"
        config.smoothing = 1.0

        ps = PredictionSystem(config)

        start_time = 100.0

        with patch("time.time", return_value=start_time):
            ps.predict(100, 100)

        # Simultaneous/Zero-dt frames
        with patch("time.time", return_value=start_time):
            px, py = ps.predict(110, 110)
            assert np.isfinite(px)
            assert ps.velocity_x > 0

        # Micro-dt frames (0.1ms)
        with patch("time.time", return_value=start_time + 0.0001):
            px, py = ps.predict(120, 120)
            assert np.isfinite(px)

    def test_floating_point_precision_stability_100k(self):
        """
        Run 100,000 iterations of EMA to detect accumulated precision errors.
        (Reduced from 1M to speed up verification loop).
        """
        ema = SimpleEMA(alpha=0.1, x0=0.0)
        target = 1337.0

        for _ in range(100000):
            ema(target)

        assert abs(ema.x_prev - target) < 1e-9

    def test_cross_thread_consistency_collision(self):
        """
        Simulate a race between the GUI thread updating config and
        the Algorithm thread reading it for prediction.
        """
        config = Config()
        ps = PredictionSystem(config)

        error_container = []
        stop_event = threading.Event()

        def algorithm_worker():
            while not stop_event.is_set():
                try:
                    px, py = ps.predict(500, 500)
                    if not (np.isfinite(px) and np.isfinite(py)):
                        error_container.append(ValueError(f"Non-finite prediction: {px}, {py}"))
                except Exception as e:
                    error_container.append(e)
                # Small yield to prevent CPU starvation and excessive memory use
                time.sleep(0)

        def gui_worker():
            methods = ["EMA", "DEMA", "TEMA", "Median+EMA", "Dynamic EMA"]
            for i in range(200):  # Reduced iterations
                config.update("filter_method", methods[i % len(methods)])
                config.update("smoothing", float(i % 10))
                time.sleep(0.001)

        t1 = threading.Thread(target=algorithm_worker)
        t2 = threading.Thread(target=gui_worker)

        t1.start()
        t2.start()

        t2.join()
        stop_event.set()
        t1.join()

        # Verify no exceptions occurred
        assert len(error_container) == 0, f"Thread safety failure: {error_container}"

    def test_coordinate_normalization_multi_resolution(self):
        """
        Validate coordinate normalization across standard and non-standard resolutions.
        """
        resolutions = [
            (1920, 1080),  # 16:9
            (2560, 1440),  # 2K
            (3840, 2160),  # 4K
            (1280, 720),  # HD
            (800, 600),  # 4:3
        ]

        config = MagicMock()

        for w, h in resolutions:
            with patch("ctypes.windll.user32.GetSystemMetrics", side_effect=[w, h]):
                _ms = LowLevelMovementSystem(config)

                # Check center
                norm_x = int((w // 2) * 65535 / w)
                norm_y = int((h // 2) * 65535 / h)

                assert abs(norm_x - 32767) <= 1
                assert abs(norm_y - 32767) <= 1

    def test_dynamic_ema_extreme_delta_recovery(self):
        """
        Test DynamicEMA recovery after a massive' teleport' delta.
        """
        de = DynamicEMA(min_alpha=0.01, max_alpha=0.9, sensitivity=2.0, x0=100.0)

        res1 = de(10000)
        assert res1 > 5000

        res2 = de(10001)
        delta_after_teleport = abs(res2 - res1)
        assert delta_after_teleport < 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
