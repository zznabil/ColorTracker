from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.detection import DetectionSystem
from utils.config import Config


class MockScreenShot:
    """Mock for mss.screenshot.ScreenShot"""

    def __init__(self, arr):
        self.height, self.width, self.channels = arr.shape
        self.raw = arr.tobytes()
        self._array = arr

    @property
    def bgra(self):
        return self.raw

    def __array__(self):
        return self._array


@pytest.fixture
def mock_detection():
    config = Config()
    config.fov_x = 50
    config.fov_y = 50
    config.screen_width = 1920
    config.screen_height = 1080
    config.target_color = 0xFF00FF  # Magenta
    config.color_tolerance = 10

    return DetectionSystem(config, MagicMock())


def test_find_target_success(mock_detection):
    """Test target finding logic using mocked MSS screen capture"""

    # Grab area will be 100x100 (fov_x=50 -> radius=50 -> width=100)
    # top-left will be (960-50, 540-50) = (910, 490)
    img = np.zeros((100, 100, 4), dtype=np.uint8)
    # Put target at (10, 10) in the cropped image
    # Screen coord should be (910+10, 490+10) = (920, 500)
    img[10:15, 10:15] = [255, 0, 255, 255]  # Magenta

    # Create the MockScreenShot object
    mock_screenshot = MockScreenShot(img)

    with patch("mss.mss") as mock_mss:
        # Return the MockScreenShot instead of raw array
        # This mocks mss inside MSSBackend
        mock_mss.return_value.grab.return_value = mock_screenshot

        # We must NOT patch _get_backend if we want to test MSSBackend logic (which uses mss)
        # However, DetectionSystem might have cached a backend or use _local
        # Ensure we are using MSS backend

        found, x, y = mock_detection.find_target()

        assert found is True
        assert x == 920
        assert y == 500


def test_find_target_no_color(mock_detection):
    """Ensure find_target returns False when target color is missing"""
    img = np.zeros((200, 200, 4), dtype=np.uint8)  # Black screen
    mock_screenshot = MockScreenShot(img)

    with patch("mss.mss") as mock_mss:
        mock_mss.return_value.grab.return_value = mock_screenshot
        found, x, y = mock_detection.find_target()
        assert found is False
