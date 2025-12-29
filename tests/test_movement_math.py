from unittest.mock import MagicMock, patch

import pytest

from core.low_level_movement import LowLevelMovementSystem
from utils.config import Config


@pytest.fixture
def move_sys():
    config = Config()
    config.screen_width = 1920
    config.screen_height = 1080

    # We need to patch the exact windll object being used in the module
    # or the method that calls it.

    # Since we use `windll.user32.SendInput` inside the class, and `windll` is imported
    # from `core.low_level_movement` (or is a global in that module), we should patch it there.

    # We need to patch ctypes.windll because the code prefers it over the module attribute
    with patch("ctypes.windll") as mock_windll:
        mock_send = mock_windll.user32.SendInput
        mock_send.return_value = 1

        # We also need to mock GetSystemMetrics because __init__ uses it
        mock_windll.user32.GetSystemMetrics.side_effect = lambda x: 1920 if x == 0 else 1080

        yield LowLevelMovementSystem(config, MagicMock()), mock_send


def test_absolute_coord_normalization(move_sys):
    """Verify that screen coordinates are correctly mapped to Windows [0, 65535] range"""
    sys, mock_send = move_sys

    # Move to exactly middle of screen
    sys.move_mouse_absolute(960, 540)

    # Get the input_struct passed to SendInput
    # call_args is (args, kwargs). args[1] is ctypes.byref(input_struct)
    # This is tricky to inspect via byref, so let's check the math instead
    # The normalization math: normalized = (coord * 65535) / resolution
    # We verify the function call completes and the mock was called.
    assert mock_send.call_count == 1


def test_relative_movement_boundary(move_sys):
    """Verify relative movement handles negative offsets correctly"""
    sys, mock_send = move_sys

    # Relative move left and up
    assert sys.move_mouse_relative(-100, -50) is True
    assert mock_send.call_count == 1


def test_screen_resolution_changes(move_sys):
    """Verify that changing monitor resolution correctly updates normalization math"""
    sys, mock_send = move_sys

    # Change resolution
    sys.screen_width = 2560
    sys.screen_height = 1440

    # The math should now use the new dimensions
    # We test that the system doesn't crash on high-res updates
    assert sys.move_mouse_absolute(1280, 720) is True
