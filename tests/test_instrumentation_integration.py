from unittest.mock import MagicMock

from core.detection import DetectionSystem
from core.low_level_movement import LowLevelMovementSystem
from utils.config import Config
from utils.performance_monitor import PerformanceMonitor


class TestInstrumentationIntegration:
    def test_detection_probes(self):
        config = MagicMock(spec=Config)
        monitor = PerformanceMonitor()

        # This should succeed now
        detection = DetectionSystem(config, monitor)

        # Mock necessary config values for detection
        config.fov_x = 100
        config.fov_y = 100
        config.screen_width = 1920
        config.screen_height = 1080
        config.target_color = 0xFF0000
        config.color_tolerance = 10

        # Spy on monitor
        monitor.start_probe = MagicMock()
        monitor.stop_probe = MagicMock()

        # MOCK _get_sct to return a fake image so capture succeeds
        # This ensures we reach the 'detection_process' probe
        mock_sct = MagicMock()
        mock_img = MagicMock()
        # Create a valid buffer for 100x100 image (BGRA)
        mock_img.bgra = b'\x00' * (100 * 100 * 4)
        mock_img.height = 100
        mock_img.width = 100
        mock_sct.grab.return_value = mock_img

        # We must mock the method on the instance
        detection._get_sct = MagicMock(return_value=mock_sct)

        # Call the method we expect to be instrumented
        try:
            # We need to ensure _scan_area is set or find_target returns early
            detection._scan_area = (0,0,100,100)
            detection.find_target() # No args, uses self.target_x/y or scan area
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
        # "detection_capture" should also be there
        assert "detection_capture" in calls

    def test_movement_probes(self):
        config = MagicMock(spec=Config)
        monitor = PerformanceMonitor()

        # This will fail on init until we fix LowLevelMovementSystem
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
