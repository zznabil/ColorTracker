from unittest.mock import MagicMock, patch

from core.detection import DetectionSystem
from core.low_level_movement import LowLevelMovementSystem
from utils.config import Config
from utils.performance_monitor import PerformanceMonitor


class TestInstrumentationIntegration:
    @patch("core.detection.mss.mss")
    def test_detection_probes(self, mock_mss_class):
        config = MagicMock(spec=Config)
        monitor = PerformanceMonitor()

        # Mock MSS instance and grab method
        mock_sct = MagicMock()
        mock_mss_class.return_value = mock_sct

        # Setup mock image return for grab
        mock_shot = MagicMock()
        # Create a valid BGRA buffer (100x100x4 bytes)
        mock_shot.bgra = b'\x00' * (100 * 100 * 4)
        mock_shot.width = 100
        mock_shot.height = 100
        mock_sct.grab.return_value = mock_shot

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

        # Call the method we expect to be instrumented
        # We need to ensure _scan_area is set or find_target returns early
        detection._scan_area = (0,0,100,100)
        detection.find_target() # No args, uses self.target_x/y or scan area

        # Verify probes were started/stopped
        # We instrumented _capture_and_process_frame ("detection_capture") and _local/_full search ("detection_process")
        # detection.find_target() calls _full_search -> _capture_and_process_frame
        assert monitor.start_probe.call_count >= 1
        assert monitor.stop_probe.call_count >= 1

        # Check specific probe names
        calls = [args[0] for args, _ in monitor.start_probe.call_args_list]
        assert "detection_process" in calls
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
