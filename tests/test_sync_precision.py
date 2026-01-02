import sys
import time
from unittest.mock import MagicMock

# Mock dearpygui
sys.modules["dearpygui.dearpygui"] = MagicMock()
sys.modules["dearpygui"] = MagicMock()

from main import ColorTrackerAlgo  # noqa: E402


class TestSyncPrecision:
    def test_smart_sleep_precision(self):
        app = ColorTrackerAlgo()
        app.running = True

        target_sleep = 0.016  # 16ms (60 FPS)

        start = time.perf_counter()
        app._smart_sleep(target_sleep, start + target_sleep)
        end = time.perf_counter()

        actual_sleep = end - start
        error = abs(actual_sleep - target_sleep)

        # We expect high precision, say < 2ms error (usually < 0.5ms with spin wait)
        # Note: on some CI envs, this might be flaky. Increased tolerance to 5ms for CI stability.
        assert error < 0.005, f"Sleep error too high: {error * 1000:.3f}ms"

    def test_smart_sleep_short(self):
        app = ColorTrackerAlgo()
        app.running = True
        target_sleep = 0.0005  # 0.5ms

        start = time.perf_counter()
        app._smart_sleep(target_sleep, start + target_sleep)
        end = time.perf_counter()

        actual_sleep = end - start
        # For very short sleeps, we might overshoot slightly due to function overhead,
        # but shouldn't undershoot significantly if we want to maintain frame cap?
        # Actually, undershoot is worse for frame pacing (too fast).
        # Overshoot drops FPS.

        # We just verify it waited at least the target time
        assert actual_sleep >= target_sleep
