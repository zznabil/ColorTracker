from unittest.mock import MagicMock, patch

import numpy as np

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

        # Mock capture so we don't need a real screen
        # We need a valid numpy array so OpenCV doesn't crash if called
        dummy_img = np.zeros((100, 100, 4), dtype=np.uint8)

        with patch.object(detection, '_capture_and_process_frame', return_value=(True, dummy_img)):
            # We need to ensure _scan_area is set or find_target returns early
            detection._scan_area = (0, 0, 100, 100)
            detection.find_target()  # No args, uses self.target_x/y or scan area

        # Verify probes were started/stopped
        # We instrumented _capture_and_process_frame ("detection_capture") and _local/_full search ("detection_process")
        # detection.find_target() calls _full_search -> _capture_and_process_frame (which is mocked, but capture probe is inside it?)
        # Wait, if we mock _capture_and_process_frame, we bypass the "detection_capture" probe which is INSIDE it!
        # So we should only see "detection_process" probe.

        # Verify "detection_process" was called (which is in _scan_region now, or _full_search before)
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
