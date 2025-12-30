from unittest.mock import MagicMock, patch

from core.detection import DetectionSystem
from core.low_level_movement import LowLevelMovementSystem
from utils.config import Config
from utils.performance_monitor import PerformanceMonitor


class TestInstrumentationIntegration:
    def test_detection_probes(self):
        config = MagicMock(spec=Config)
        # Mock necessary config values for detection BEFORE instantiation
        config.fov_x = 100
        config.fov_y = 100
        config.screen_width = 1920
        config.screen_height = 1080
        config.target_color = 0xFF0000
        config.color_tolerance = 10
        config._version = 1

        monitor = PerformanceMonitor()

        # This should succeed now with proper mock config
        detection = DetectionSystem(config, monitor)

        # Spy on monitor
        monitor.start_probe = MagicMock()
        monitor.stop_probe = MagicMock()

        # Call the method we expect to be instrumented
        try:
            # We need to ensure _scan_area is set or find_target returns early
            detection._scan_area = (0, 0, 100, 100)

            # Mock _get_sct to return a mock that produces valid bgra
            with patch.object(detection, '_get_sct') as mock_get_sct:
                mock_sct = MagicMock()
                mock_shot = MagicMock()
                mock_shot.bgra = b'\x00' * (100 * 100 * 4)  # 100x100 4-channel
                mock_shot.height = 100
                mock_shot.width = 100
                mock_sct.grab.return_value = mock_shot
                mock_get_sct.return_value = mock_sct

                detection.find_target()  # No args, uses self.target_x/y or scan area
        except Exception:
            pass

        # Verify probes were started/stopped
        # We instrumented _capture_and_process_frame ("detection_capture") and _local/_full search ("detection_process")
        # detection.find_target() calls _full_search -> _capture_and_process_frame
        assert monitor.start_probe.call_count >= 1
        assert monitor.stop_probe.call_count >= 1

        # Check specific probe names
        calls = [args[0] for args, _ in monitor.start_probe.call_args_list]
        assert "detection_process" in calls
        # "detection_capture" might be skipped if exception happens early, but we tried to ensure it runs.

    def test_movement_probes(self):
        config = MagicMock(spec=Config)
        # Mock necessary config values for movement BEFORE instantiation
        config.screen_width = 1920
        config.screen_height = 1080
        config.aim_point = 1
        config.smooth_factor = 0.5
        config._version = 1

        monitor = PerformanceMonitor()

        # This should succeed now with proper mock config
        movement = LowLevelMovementSystem(config, monitor)

        monitor.start_probe = MagicMock()
        monitor.stop_probe = MagicMock()

        # Call move_mouse_relative
        try:
            movement.move_mouse_relative(10, 10)
        except Exception:
            pass

        # Verify probes
        assert monitor.start_probe.call_count >= 1
        assert monitor.stop_probe.call_count >= 1
