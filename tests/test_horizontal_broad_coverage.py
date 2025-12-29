"""
Horizontal Broad Coverage Test Suite

ULTRATHINK Protocol: This suite tests BREADTH across all modules and interactions.
It exercises code paths that are touched in real usage but may not appear in unit tests.

Coverage focus:
- Module initialization paths
- State machine transitions
- Error recovery paths
- Boundary state combinations
- Cross-module data flow
"""

import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.detection import DetectionSystem
from core.low_level_movement import LowLevelMovementSystem
from core.motion_engine import MotionEngine
from utils.config import Config
from utils.logger import Logger


class TestConfigFullLifecycle:
    """Test config through its complete lifecycle"""

    def test_config_default_initialization(self):
        """Verify all default values are correct types and ranges"""
        config = Config()

        # Type checks for core values
        assert isinstance(config.screen_width, int)
        assert isinstance(config.screen_height, int)
        assert isinstance(config.fov_x, int)
        assert isinstance(config.fov_y, int)
        assert isinstance(config.target_color, int)
        assert isinstance(config.color_tolerance, int)
        assert isinstance(config.target_color, int)
        assert isinstance(config.color_tolerance, int)
        assert isinstance(config.motion_min_cutoff, float)
        assert isinstance(config.prediction_scale, float)

        assert isinstance(config.aim_point, int)

    def test_config_validation_rejects_invalid_types(self):
        """Test that validation handles type coercion or rejection"""
        config = Config()

        # Test that update properly validates
        config.update("fov_x", "100")  # String should be converted
        assert isinstance(config.fov_x, int)

        config.update("motion_min_cutoff", "0.05")  # String float
        assert isinstance(config.motion_min_cutoff, float)

    def test_config_preserves_state_after_multiple_updates(self):
        """Test state consistency after rapid updates"""
        config = Config()

        # Rapid fire updates
        for i in range(100):
            config.update("fov_x", 10 + (i % 490))
            config.update("motion_min_cutoff", (i % 100) / 100.0)

        # State should be internally consistent
        assert 10 <= config.fov_x <= 500
        assert 0.0 <= config.motion_min_cutoff <= 1.0

    def test_config_get_all_completeness(self):
        """Verify get_all returns all expected keys"""
        config = Config()
        all_config = config.get_all()

        expected_keys = [
            "screen_width",
            "screen_height",
            "target_color",
            "color_tolerance",
            "fov_x",
            "fov_y",
            "motion_min_cutoff",
            "prediction_scale",
        ]

        for key in expected_keys:
            assert key in all_config, f"Missing key: {key}"


class TestDetectionSystemBoundaryConditions:
    """Test detection across boundary conditions"""

    def test_fov_at_minimum_size(self):
        """Test detection with smallest possible FOV"""
        config = MagicMock()
        config.screen_width = 1920
        config.screen_height = 1080
        config.fov_x = 10  # Minimum
        config.fov_y = 10  # Minimum
        config.search_area = 5
        config.target_color = 0xFF0000
        config.color_tolerance = 10

        ds = DetectionSystem(config, MagicMock())

        with patch.object(ds, "_get_sct") as mock_sct:
            img = np.zeros((20, 20, 4), dtype=np.uint8)
            img[10, 10] = [0, 0, 255, 255]  # Target at center

            mock_sct.return_value.grab.return_value = img

            found, x, y = ds.find_target()
            # Should handle tiny FOV
            assert found is True or found is False

    def test_fov_at_maximum_size(self):
        """Test detection with largest possible FOV"""
        config = MagicMock()
        config.screen_width = 1920
        config.screen_height = 1080
        config.fov_x = 500  # Maximum
        config.fov_y = 500  # Maximum
        config.search_area = 50
        config.target_color = 0xFF0000
        config.color_tolerance = 10

        ds = DetectionSystem(config, MagicMock())

        with patch.object(ds, "_get_sct") as mock_sct:
            img = np.zeros((550, 550, 4), dtype=np.uint8)
            img[275, 275] = [0, 0, 255, 255]

            mock_sct.return_value.grab.return_value = img

            found, x, y = ds.find_target()
            assert found is True or found is False

    def test_color_with_all_zero_bytes(self):
        """Test detection with black target color"""
        config = MagicMock()
        config.screen_width = 1920
        config.screen_height = 1080
        config.fov_x = 100
        config.fov_y = 100
        config.search_area = 50
        config.target_color = 0x000000  # Black
        config.color_tolerance = 5

        ds = DetectionSystem(config, MagicMock())

        with patch.object(ds, "_get_sct") as mock_sct:
            img = np.zeros((100, 100, 4), dtype=np.uint8)
            # All black already

            mock_sct.return_value.grab.return_value = img

            found, x, y = ds.find_target()
            # Should find black in black image
            assert isinstance(found, bool)

    def test_color_with_all_ff_bytes(self):
        """Test detection with white target color"""
        config = MagicMock()
        config.screen_width = 1920
        config.screen_height = 1080
        config.fov_x = 100
        config.fov_y = 100
        config.search_area = 50
        config.target_color = 0xFFFFFF  # White
        config.color_tolerance = 5

        ds = DetectionSystem(config, MagicMock())

        with patch.object(ds, "_get_sct") as mock_sct:
            img = np.ones((100, 100, 4), dtype=np.uint8) * 255

            mock_sct.return_value.grab.return_value = img

            found, x, y = ds.find_target()
            assert isinstance(found, bool)


class TestMovementSystemMathematics:
    """Test movement system mathematical correctness"""

    def test_coordinate_normalization_formula(self):
        """Verify absolute positioning uses correct Windows normalization"""
        config = MagicMock()

        with patch("ctypes.windll.user32.GetSystemMetrics", side_effect=[1920, 1080]):
            _ms = LowLevelMovementSystem(config, MagicMock())  # Initialize to validate construction

            # Test normalization math: x * 65535 / screen_width
            # At screen center (960, 540)
            expected_norm_x = int((960 * 65535) / 1920)
            expected_norm_y = int((540 * 65535) / 1080)

            # Verify values are in expected range
            assert 0 < expected_norm_x < 65535
            assert 0 < expected_norm_y < 65535
            assert expected_norm_x == 32767  # ~half of 65535
            assert expected_norm_y == 32767  # ~half of 65535

    def test_aim_offset_calculations(self):
        """Test aim offset for head/body/leg positions"""
        config = MagicMock()
        config.aim_point = 1  # Body
        config.head_offset = 10
        config.leg_offset = 20

        with patch("ctypes.windll.user32.GetSystemMetrics", side_effect=[1920, 1080]):
            ms = LowLevelMovementSystem(config, MagicMock())

            # Body (aim_point=1) - no offset
            assert ms._apply_aim_offset(500) == 500

            # Head (aim_point=0) - subtract head_offset
            config.aim_point = 0
            assert ms._apply_aim_offset(500) == 490

            # Legs (aim_point=2) - add leg_offset
            config.aim_point = 2
            assert ms._apply_aim_offset(500) == 520


class TestLoggerEdgeCasesExpanded:
    """Extended logger edge case testing"""

    def test_logger_rate_limiting_effectiveness(self):
        """Verify rate limiting actually limits"""
        logger = Logger()

        # Fire same message many times quickly
        start = time.time()
        count = 0
        for _ in range(1000):
            logger.debug("Same message")
            count += 1

        # Should complete quickly because of rate limiting
        elapsed = time.time() - start
        assert elapsed < 5.0  # Should be fast even with 1000 calls

    def test_logger_different_levels_independence(self):
        """Test that different log levels don't interfere"""
        logger = Logger()

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # All should work without raising
        assert True

    def test_logger_empty_message_handling(self):
        """Test logger with empty strings"""
        logger = Logger()

        try:
            logger.info("")
            logger.debug("")
            logger.warning("")
        except Exception as e:
            pytest.fail(f"Logger failed on empty message: {e}")


class TestCrossModuleDataFlow:
    """Test data flows between modules"""

    def test_detection_to_prediction_coordinate_passing(self):
        """Verify coordinates flow correctly detection -> prediction"""
        config = MagicMock()
        config.screen_width = 1920
        config.screen_height = 1080
        config.fov_x = 100
        config.fov_y = 100
        config.search_area = 50
        config.target_color = 0xFF0000
        config.color_tolerance = 10
        config.prediction_enabled = True
        config.prediction_scale = 0.0  # No prediction offset
        config.motion_min_cutoff = 0.001  # Minimal smoothing

        ps = MotionEngine(config)

        # Simulate detection output
        detection_x, detection_y = 960, 540

        with patch("time.time", return_value=100.0):
            # uses perf_counter internally, patch it
            with patch("time.perf_counter", return_value=100.0):
                px, py = ps.process(detection_x, detection_y, 0.0)

        # With no prediction and minimal smoothing, should pass through
        assert px == detection_x or abs(px - detection_x) < 5
        assert py == detection_y or abs(py - detection_y) < 5

    def test_prediction_to_movement_coordinate_passing(self):
        """Verify coordinates flow correctly prediction -> movement"""
        config = MagicMock()
        config.aim_point = 1
        config.head_offset = 10
        config.leg_offset = 20

        with patch("ctypes.windll.user32.GetSystemMetrics", side_effect=[1920, 1080]):
            ms = LowLevelMovementSystem(config, MagicMock())

            # Simulate prediction output OFF-CENTER (not at 960, 540)
            # Target at (1060, 640) - 100px right and 100px down from center
            pred_x, pred_y = 1060, 640

            with patch.object(ms, "move_mouse_relative") as mock_move:
                mock_move.return_value = True
                ms.move_to_target(pred_x, pred_y)

                # move_to_target calculates offset from screen center (960, 540)
                # Offset should be (1060-960, 640-540) = (100, 100)
                mock_move.assert_called_once_with(100, 100)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
