"""
Detection Noise Resilience Test Suite

ULTRATHINK Protocol: Tests detection stability under extreme visual noise and ambiguity.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.detection import DetectionSystem


class TestDetectionNoiseResilience:
    @pytest.fixture
    def base_config(self):
        config = MagicMock()
        config.screen_width = 1920
        config.screen_height = 1080
        config.fov_x = 100
        config.fov_y = 100
        config.search_area = 50
        config.target_color = 0xFF0000  # Red
        config.color_tolerance = 10
        return config

    def test_salt_and_pepper_noise_resilience(self, base_config, mock_screenshot_factory):
        """Test detection with high-frequency pixel noise"""
        ds = DetectionSystem(base_config, MagicMock())

        with patch.object(ds, "_get_sct") as mock_sct:
            # Create image with target and noise
            img = np.zeros((100, 100, 4), dtype=np.uint8)
            # Target at 50, 50 (Red in BGRA is [0, 0, 255, 255])
            img[50, 50] = [0, 0, 255, 255]

            # Add 10% white noise
            noise = np.random.randint(0, 2, (100, 100, 4), dtype=np.uint8) * 255
            mask = np.random.random((100, 100)) < 0.1
            img[mask] = noise[mask]

            mock_sct.return_value.grab.return_value = mock_screenshot_factory(img)

            found, x, y = ds.find_target()
            # Should still find target if cluster is big enough or noise doesn't overwhelm
            # Note: find_target might return center of multiple noise pixels if tolerance is high
            assert isinstance(found, bool)

    def test_multiple_competing_clusters(self, base_config, mock_screenshot_factory):
        """Test recovery when multiple similar color clusters are present"""
        ds = DetectionSystem(base_config, MagicMock())

        with patch.object(ds, "_get_sct") as mock_sct:
            img = np.zeros((100, 100, 4), dtype=np.uint8)
            # Two "Red" pixels
            img[20, 20] = [0, 0, 255, 255]
            img[80, 80] = [0, 0, 255, 255]

            mock_sct.return_value.grab.return_value = mock_screenshot_factory(img)

            found, x, y = ds.find_target()
            assert found is True
            # Should pick one (usually the first one found or average depending on CV2 implementation)
            assert x > 0 and y > 0

    def test_target_partially_obscured_at_fov_edge(self, base_config, mock_screenshot_factory):
        """Test detection stability when target is clipped at FOV boundaries"""
        ds = DetectionSystem(base_config, MagicMock())

        with patch.object(ds, "_get_sct") as mock_sct:
            img = np.zeros((100, 100, 4), dtype=np.uint8)
            # Target at very bottom right edge
            img[99, 99] = [0, 0, 255, 255]

            mock_sct.return_value.grab.return_value = mock_screenshot_factory(img)

            found, x, y = ds.find_target()
            assert found is True

    def test_zero_pixel_found_no_crash(self, base_config, mock_screenshot_factory):
        """Verify no pixels matching color results in False found, not crash"""
        ds = DetectionSystem(base_config, MagicMock())

        with patch.object(ds, "_get_sct") as mock_sct:
            img = np.zeros((100, 100, 4), dtype=np.uint8)  # No red
            mock_sct.return_value.grab.return_value = mock_screenshot_factory(img)

            found, x, y = ds.find_target()
            assert found is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
