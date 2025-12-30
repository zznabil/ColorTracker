import threading
import time
from collections import deque

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
        assert monitor.detection_times[0] == 5.0  # 5ms

    def test_get_stats(self):
        monitor = PerformanceMonitor()

        # Add some data
        monitor.record_frame(0.010, missed=False)  # 10ms
        monitor.record_frame(0.020, missed=True)  # 20ms
        monitor.record_detection(0.005)  # 5ms

        # Mock time to force FPS calculation
        start = time.perf_counter()
        monitor._last_fps_update = start - 1.0  # 1 second ago
        monitor._frame_counter = 60
        monitor.record_frame(0.010)  # Trigger update

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

    def test_get_stats_comprehensive(self):
        """Test get_stats with enough data for 1% lows."""
        monitor = PerformanceMonitor(history_size=200)

        # Fill history with 150 frames
        # 140 frames at 10ms (100 FPS)
        # 10 frames at 100ms (10 FPS) -> these will be the 1% lows
        for _ in range(140):
            monitor.record_frame(0.010)
        for _ in range(10):
            monitor.record_frame(0.100)

        stats = monitor.get_stats()

        assert stats["avg_frame_ms"] == (140 * 10 + 10 * 100) / 150
        assert stats["worst_frame_ms"] == 100.0
        # 1% of 150 is 1.5 -> index 1 in sorted descending
        # sorted_times[1] should be 100.0
        assert stats["one_percent_low_fps"] == 10.0  # 1000 / 100.0


    def test_reset_aggregates(self):
        monitor = PerformanceMonitor()
        monitor.record_frame(0.100, missed=True)  # 100ms

        assert monitor.worst_frame_time == 100.0
        assert monitor.missed_frames == 1

        monitor.reset_aggregates()

        assert monitor.worst_frame_time == 0.0
        assert monitor.missed_frames == 0
        # History should persist
        assert len(monitor.frame_times) == 1

    # New tests for telemetry probe methods
    def test_start_stop_probe_basic(self):
        """Test basic probe start/stop functionality."""
        monitor = PerformanceMonitor()

        # Start a probe
        monitor.start_probe("test_operation")
        assert "test_operation" in monitor._active_probes

        # Stop the probe
        time.sleep(0.01)  # Small delay to ensure measurable duration
        monitor.stop_probe("test_operation")
        assert "test_operation" not in monitor._active_probes

        # Check that duration was recorded
        history = monitor._probe_history["test_operation"]
        assert len(history) == 1
        assert history[0] > 0  # Should have positive duration in ms

    def test_stop_nonexistent_probe(self):
        """Test stopping a probe that doesn't exist."""
        monitor = PerformanceMonitor()

        # Should not raise exception
        monitor.stop_probe("nonexistent_probe")

        # No history should be created
        assert "nonexistent_probe" not in monitor._probe_history

    def test_multiple_probes_concurrent(self):
        """Test running multiple probes concurrently."""
        monitor = PerformanceMonitor()

        # Start multiple probes
        monitor.start_probe("operation_a")
        monitor.start_probe("operation_b")
        monitor.start_probe("operation_c")

        assert len(monitor._active_probes) == 3

        # Stop them in different order
        time.sleep(0.01)
        monitor.stop_probe("operation_b")
        time.sleep(0.01)
        monitor.stop_probe("operation_a")
        time.sleep(0.01)
        monitor.stop_probe("operation_c")

        # Check all recorded durations
        assert len(monitor._probe_history["operation_a"]) == 1
        assert len(monitor._probe_history["operation_b"]) == 1
        assert len(monitor._probe_history["operation_c"]) == 1

        # Operation C should have longest duration (stopped last)
        assert monitor._probe_history["operation_c"][0] > monitor._probe_history["operation_b"][0]

    def test_probe_stats_calculation(self):
        """Test probe statistics calculation."""
        monitor = PerformanceMonitor()

        # Record multiple probe durations
        durations = [1.0, 2.0, 3.0, 4.0, 5.0]  # ms
        for duration in durations:
            monitor._probe_history["test"].append(duration)

        stats = monitor.get_probe_stats("test")

        assert stats["avg_ms"] == 3.0  # (1+2+3+4+5)/5
        assert stats["min_ms"] == 1.0
        assert stats["max_ms"] == 5.0
        assert stats["count"] == 5

    def test_probe_stats_empty(self):
        """Test probe stats for non-existent probe."""
        monitor = PerformanceMonitor()

        stats = monitor.get_probe_stats("nonexistent")
        assert stats == {}

    def test_probe_history_limit(self):
        """Test that probe history respects maxlen limit."""
        # Use a large history size for the monitor, but specific probes will still use it
        monitor = PerformanceMonitor(history_size=1000)

        # Test a specific probe's history
        probe_name = "limit_test"
        # Since PerformanceMonitor uses history_size for ALL deques in _probe_history
        # we test if it prunes after history_size items
        monitor = PerformanceMonitor(history_size=5)

        for _i in range(10):
            monitor.start_probe(probe_name)
            monitor.stop_probe(probe_name)

        assert len(monitor._probe_history[probe_name]) == 5

    def test_high_resolution_timing(self):
        """Test that probes use high-resolution timing."""
        monitor = PerformanceMonitor()

        # Start and stop probe very quickly
        monitor.start_probe("fast_operation")
        monitor.stop_probe("fast_operation")

        # Should still capture some duration (even if very small)
        duration = monitor._probe_history["fast_operation"][0]
        assert duration >= 0

        # Test that we can measure durations with stability
        monitor.start_probe("stable_ms")
        time.sleep(0.005)  # 5ms
        monitor.stop_probe("stable_ms")

        stable_duration = monitor._probe_history["stable_ms"][0]
        # Should be around 5ms, allow wide range for CI variance
        assert 1.0 < stable_duration < 50.0

    def test_concurrent_probe_safety(self):
        """Test that probes are thread-safe for basic operations."""
        monitor = PerformanceMonitor()
        results = []

        def worker(thread_id):
            for i in range(10):
                probe_name = f"thread_{thread_id}_op_{i}"
                monitor.start_probe(probe_name)
                time.sleep(0.001)
                monitor.stop_probe(probe_name)
                results.append(probe_name)

        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all probes were recorded
        assert len(results) == 30  # 3 threads * 10 operations each

        # Check that we have data for all probe names
        for probe_name in results:
            assert probe_name in monitor._probe_history
            assert len(monitor._probe_history[probe_name]) == 1

    def test_probe_memory_efficiency(self):
        """Test that probes don't create excessive memory allocations."""
        monitor = PerformanceMonitor()

        # Record many probe measurements
        for _i in range(1000):
            monitor.start_probe("memory_test")
            monitor.stop_probe("memory_test")

        # History should be limited by maxlen
        assert len(monitor._probe_history["memory_test"]) <= monitor.history_size

        # Verify deque is being used (efficient memory usage)
        assert isinstance(monitor._probe_history["memory_test"], deque)

    def test_nested_probe_error_handling(self):
        """Test behavior when starting same probe twice."""
        monitor = PerformanceMonitor()

        # Start same probe twice
        monitor.start_probe("duplicate_test")
        monitor.start_probe("duplicate_test")  # Should overwrite

        # Stop it
        monitor.stop_probe("duplicate_test")

        # Should have exactly one measurement
        assert len(monitor._probe_history["duplicate_test"]) == 1
        assert "duplicate_test" not in monitor._active_probes

class TestProbeEmptyHistory:
    def test_empty_probe_stats(self):
        """Test that empty probe history returns empty dict without errors."""
        monitor = PerformanceMonitor()
        stats = monitor.get_probe_stats("never_started")
        assert stats == {}
        assert isinstance(stats, dict)

    def test_started_but_not_stopped_probe(self):
        """Test that started but not stopped probe returns empty stats."""
        monitor = PerformanceMonitor()
        monitor.start_probe("incomplete")
        stats = monitor.get_probe_stats("incomplete")
        assert stats == {}
