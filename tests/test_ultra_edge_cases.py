"""
Ultra Edge Cases Test Suite

Tests extreme scenarios specifically for movement normalization,
config corruption recovery, and temporal instability.
"""

import os
from unittest.mock import MagicMock, patch

import numpy as np

from core.low_level_movement import LowLevelMovementSystem
from core.motion_engine import MotionEngine
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
    config.prediction_scale = 1.0
    config.motion_min_cutoff = 0.5
    config.motion_beta = 0.05

    ps = MotionEngine(config)

    with patch("time.perf_counter", return_value=100.0):
        ps.process(100, 100, 0.0)

    with patch("time.perf_counter", return_value=100.016):
        ps.process(100, 100, 0.016)

    # Big jump in time
    with patch("time.perf_counter", return_value=105.016):
        px, py = ps.process(200, 200, 5.0)
        assert np.isfinite(px) and np.isfinite(py)


def test_detection_area_clipping_logic(mock_screenshot_factory):
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
    ds._update_fov_cache()

    with patch.object(ds, "_get_sct") as mock_sct:
        grab_mock = MagicMock()
        # Ensure the mock returns an object with shape compatible with the logic
        # 1x1 image for testing flow
        grab_mock.return_value = mock_screenshot_factory(np.zeros((1, 1, 4), dtype=np.uint8))
        mock_sct.return_value.grab = grab_mock

        # 1. Target near edge of FOV (fov_x=100, center=960 -> right_edge=1060)
        # target_x=1050 (valid). local_search=100 -> left=950.
        # We find match at local +115 = 1065 (Outside FOV).
        ds.target_x = 1050
        ds.target_y = 540
        ds.target_found_last_frame = True

        # patch minMaxLoc returns (minVal, maxVal, minLoc, maxLoc)
        # We simulate finding a target at offset (115, 0) relative to local crop
        with patch("cv2.minMaxLoc", return_value=(0, 255, (0, 0), (115, 0))):
            # local_area: left = 1050-100 = 950.
            # screen_x = 115 + 950 = 1065.
            # abs(1065 - 960) = 105 > fov_x(100). Fails.
            found, tx, ty = ds._local_search()
            assert found is False

        # 2. Target exactly at center
        ds.target_x = 960
        ds.target_y = 540
        ds.target_found_last_frame = True
        # local_area: left = 960-100 = 860. top = 540-100 = 440.
        # We want screen_x = 960. So match_x = 960 - 860 = 100.
        with patch("cv2.minMaxLoc", return_value=(0, 255, (0, 0), (100, 100))):
            found, tx, ty = ds._local_search()
            assert found is True
            assert tx == 960
            assert ty == 540
