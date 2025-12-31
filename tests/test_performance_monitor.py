import time

from utils.performance_monitor import PerformanceMonitor


class TestPerformanceMonitor:
    def test_initialization(self):
        monitor = PerformanceMonitor(history_size=100)
        assert monitor.history_size == 100
        assert len(monitor.frame_times) == 0
        assert len(monitor.fps_history) == 0

    def test_record_frame_and_fps(self):
        monitor = PerformanceMonitor()

        # Simulate a frame
        monitor.record_frame(0.016, missed=False)
        assert monitor.total_frames == 1
        assert monitor.missed_frames == 0
        assert len(monitor.frame_times) == 1
        assert monitor.frame_times[0] == 16.0  # 0.016s = 16.0ms

        # Simulate a missed frame
        monitor.record_frame(0.020, missed=True)
        assert monitor.total_frames == 2
        assert monitor.missed_frames == 1

    def test_record_detection(self):
        monitor = PerformanceMonitor()
        monitor.record_detection(0.005)

        assert len(monitor.detection_times) == 1
        assert monitor.detection_times[0] == 5.0 # 5ms

    def test_get_stats(self):
        monitor = PerformanceMonitor()

        # Add some data
        monitor.record_frame(0.010, missed=False) # 10ms
        monitor.record_frame(0.020, missed=True)  # 20ms
        monitor.record_detection(0.005) # 5ms

        # Mock time to force FPS calculation
        start = time.perf_counter()
        monitor._last_fps_update = start - 1.0 # 1 second ago
        monitor._frame_counter = 60
        monitor.record_frame(0.010) # Trigger update

        stats = monitor.get_stats()

        assert "fps" in stats
        assert "avg_frame_ms" in stats
        assert "worst_frame_ms" in stats
        assert "avg_detection_ms" in stats
        assert "missed_frames" in stats

        # Check values
        assert stats["worst_frame_ms"] >= 20.0
        assert stats["missed_frames"] == 1
        assert stats["avg_detection_ms"] == 5.0

    def test_reset_aggregates(self):
        monitor = PerformanceMonitor()
        monitor.record_frame(0.100, missed=True) # 100ms

        assert monitor.worst_frame_time == 100.0
        assert monitor.missed_frames == 1

        monitor.reset_aggregates()

        assert monitor.worst_frame_time == 0.0
        assert monitor.missed_frames == 0
        # History should persist
        assert len(monitor.frame_times) == 1
