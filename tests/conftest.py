import ctypes
import sys
from unittest.mock import MagicMock

import pytest


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
