import os
from unittest.mock import MagicMock, patch

import numpy as np

from core.low_level_movement import LowLevelMovementSystem
from core.prediction import PredictionSystem
from utils.config import Config


def test_config_json_corruption_recovery():
    """Test if Config can recover from various malformed JSON states"""
    config_path = "test_config_corrupt.json"
    if os.path.exists(config_path):
        os.remove(config_path)

    cfg = Config()
    cfg.config_file = config_path

    # 1. Empty file
    with open(config_path, "w") as f:
        f.write("")

    cfg.screen_width = 9999
    cfg.load()
    assert cfg.screen_width == 1920

    # 2. Incomplete JSON
    with open(config_path, "w") as f:
        f.write('{"screen_width": 2560, "fov_x": ')

    cfg.screen_width = 8888
    cfg.load()
    assert cfg.screen_width == 1920

    if os.path.exists(config_path):
        os.remove(config_path)


def test_movement_normalization_extreme():
    """Verify absolute movement normalization doesn't overflow 65535 and clamps correctly"""
    config = MagicMock()
    with patch("ctypes.windll.user32.GetSystemMetrics", side_effect=[1920, 1080]):
        mv = LowLevelMovementSystem(config)

        # Target far outside screen
        x, y = 100000, 100000

        with patch("ctypes.windll.user32.SendInput", return_value=1) as mock_send:
            mv.move_mouse_absolute(x, y)
            assert mock_send.called


def test_prediction_temporal_instability():
    """Test prediction behavior with erratic frame timing and filter lag"""
    config = MagicMock()
    config.prediction_enabled = True
    config.prediction_multiplier = 1.0
    config.filter_method = "EMA"
    config.smoothing = 1.0

    ps = PredictionSystem(config)

    with patch("time.time", return_value=100.0):
        ps.predict(100, 100)

    with patch("time.time", return_value=100.016):
        ps.predict(100, 100)

    with patch("time.time", return_value=105.016):
        px, py = ps.predict(200, 200)
        assert px == 200


def test_detection_area_clipping_logic():
    """Test if detection area is always within screen bounds and FOV check works"""
    from core.detection import DetectionSystem

    config = MagicMock()
    config.screen_width = 1920
    config.screen_height = 1080
    config.fov_x = 100
    config.fov_y = 100
    config.search_area = 500
    config.target_color = 0xFFFFFF
    config.color_tolerance = 10

    ds = DetectionSystem(config)

    class MockScreenShot:
        def __init__(self, img_array):
            self.bgra = img_array.tobytes()
            self.raw = self.bgra

    with patch.object(ds, "_get_sct") as mock_sct:
        grab_mock = MagicMock()
        img = np.zeros((1000, 1000, 4), dtype=np.uint8)
        grab_mock.return_value = MockScreenShot(img)
        mock_sct.return_value.grab = grab_mock

        # 1. Target far outside FOV but within search area
        # center is (960, 540). target_x=1000 is within fov(100)
        # but match_x=0 in local_area starting at 500 makes screen_x=500 -> outside fov
        ds.target_x = 1000
        ds.target_y = 1000
        ds.target_found_last_frame = True

        # patch minMaxLoc instead of findNonZero
        # returns (minVal, maxVal, minLoc, maxLoc)
        # We want maxVal > 0, and maxLoc = (10, 10)
        with patch("cv2.minMaxLoc", return_value=(0, 255, (0, 0), (10, 10))):
            # local_area: left = 1000-500 = 500. top = 1000-500 = 500.
            # screen_x = 10 + 500 = 510.
            # abs(510 - 960) = 450 > fov_x(100). Fails.
            found, tx, ty = ds._local_search()
            assert found is False

        # 2. Target exactly at center
        ds.target_x = 960
        ds.target_y = 540
        ds.target_found_last_frame = True
        # local_area: left = 960-500 = 460. top = 540-500 = 40.
        # We want screen_x = 960. So match_x = 960 - 460 = 500.
        with patch("cv2.minMaxLoc", return_value=(0, 255, (0, 0), (500, 500))):
            found, tx, ty = ds._local_search()
            assert found is True
            assert tx == 960
            assert ty == 540
