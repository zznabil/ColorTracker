import ctypes
from unittest.mock import MagicMock

# Inject a mock windll if it doesn't exist (i.e. on Linux)
if not hasattr(ctypes, "windll"):
    ctypes.windll = MagicMock()
    # Also need to mock user32 and its methods
    ctypes.windll.user32 = MagicMock()
    ctypes.windll.user32.GetSystemMetrics.return_value = 1920
    ctypes.windll.user32.GetCursorPos.return_value = 1
    ctypes.windll.user32.SendInput.return_value = 1
