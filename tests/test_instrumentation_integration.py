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

            # Mock _capture_and_process_frame to return success so it reaches "detection_process"
            # We must mock it on the instance 'detection'
            mock_img = MagicMock()
            # It needs to behave like numpy array for cv2.inRange
            detection._capture_and_process_frame = MagicMock(return_value=(True, mock_img))

            # Also mock cv2.inRange/minMaxLoc to avoid OpenCV errors with MagicMock image
            with patch("cv2.inRange"), \
                 patch("cv2.minMaxLoc", return_value=(0, 1, (0,0), (10,10))):
                detection.find_target()  # No args, uses self.target_x/y or scan area
        except Exception:
            pass

        # Verify probes were started/stopped
        # We instrumented _capture_and_process_frame ("detection_capture") and _local/_full search ("detection_process")
        # detection.find_target() calls _full_search -> _capture_and_process_frame

        # Note: Since we mocked _capture_and_process_frame, "detection_capture" probe inside it won't run.
        # But "detection_process" inside _full_search SHOULD run.

        # Verify stop_probe was called at least once
        assert monitor.stop_probe.call_count >= 1

        # Check specific probe names
        calls = [args[0] for args, _ in monitor.start_probe.call_args_list]
        assert "detection_process" in calls

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
