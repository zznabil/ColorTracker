from unittest.mock import MagicMock
import numpy as np

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

        # Mock _capture_and_process_frame to return success so the logic proceeds to "detection_process"
        # We need to return a valid 4-channel BGRA numpy array
        fake_img = np.zeros((100, 100, 4), dtype=np.uint8)
        detection._capture_and_process_frame = MagicMock(return_value=(True, fake_img))

        # Spy on monitor
        monitor.start_probe = MagicMock()
        monitor.stop_probe = MagicMock()

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
        # "detection_capture" is not called because we mocked _capture_and_process_frame
        # wait, we mocked it on the instance, so it should be fine.

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
