import sys
from unittest.mock import MagicMock

# Mock modules before they are imported
sys.modules["pyautogui"] = MagicMock()
sys.modules["mouseinfo"] = MagicMock()
sys.modules["pynput"] = MagicMock()
sys.modules["pynput.keyboard"] = MagicMock()
sys.modules["pynput.mouse"] = MagicMock()
sys.modules["dearpygui"] = MagicMock()
sys.modules["dearpygui.dearpygui"] = MagicMock()

# Configure specific mocks if needed
sys.modules["pyautogui"].position.return_value = (0, 0)
sys.modules["pyautogui"].size.return_value = (1920, 1080)
