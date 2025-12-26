import ctypes
import sys
from unittest.mock import MagicMock

import pytest


class MockScreenShot:
    """Mock for mss.screenshot.ScreenShot compatible with np.frombuffer optimizations"""
    def __init__(self, arr):
        # arr should be (H, W, 4)
        self.height, self.width, self.channels = arr.shape
        self.raw = arr.tobytes()
        self._array = arr

    @property
    def bgra(self):
        return self.raw

    def __array__(self):
        return self._array


@pytest.fixture
def mock_screenshot_factory():
    def _create(arr):
        return MockScreenShot(arr)
    return _create


@pytest.fixture(autouse=True)
def mock_windows_api(monkeypatch):
    """
    Mock Windows API calls for non-Windows environments.
    This runs automatically for all tests.
    """
    if sys.platform != "win32":
        # Create a mock for windll
        mock_windll = MagicMock()

        # Configure GetSystemMetrics to return standard screen resolution
        def get_system_metrics(n):
            return 1920 if n == 0 else 1080

        mock_windll.user32.GetSystemMetrics.side_effect = get_system_metrics

        # Configure GetCursorPos
        def get_cursor_pos(point_ptr):
            if hasattr(point_ptr, "contents"):
                point_ptr.contents.x = 960
                point_ptr.contents.y = 540
            return 1

        mock_windll.user32.GetCursorPos.side_effect = get_cursor_pos
        mock_windll.user32.SendInput.return_value = 1

        # Apply the mock to ctypes
        if not hasattr(ctypes, "windll"):
            monkeypatch.setattr(ctypes, "windll", mock_windll, raising=False)
