import time

import pytest

from utils.performance_monitor import PerformanceMonitor


class TestTelemetryProbes:
    def test_probe_lifecycle(self):
        monitor = PerformanceMonitor()
        probe_name = "test_probe"

        # Start probe
        monitor.start_probe(probe_name)

        # Simulate work
        time.sleep(0.001)

        # Stop probe
        monitor.stop_probe(probe_name)

        # Check if data was recorded
        stats = monitor.get_probe_stats(probe_name)
        assert stats is not None
        assert "avg_ms" in stats
        assert "min_ms" in stats
        assert "max_ms" in stats
        assert stats["count"] == 1
        assert stats["avg_ms"] > 0

    def test_multiple_probes(self):
        monitor = PerformanceMonitor()

        monitor.start_probe("probe_a")
        monitor.start_probe("probe_b")

        monitor.stop_probe("probe_a")
        monitor.stop_probe("probe_b")

        stats_a = monitor.get_probe_stats("probe_a")
        stats_b = monitor.get_probe_stats("probe_b")

        assert stats_a["count"] == 1
        assert stats_b["count"] == 1

    def test_probe_overwrite(self):
        """Ensure starting a probe that is already running resets the start time."""
        monitor = PerformanceMonitor()
        name = "overwrite_test"

        monitor.start_probe(name)
        first_start = monitor._active_probes[name]

        time.sleep(0.001)
        monitor.start_probe(name)
        second_start = monitor._active_probes[name]

        assert second_start > first_start

        monitor.stop_probe(name)
        stats = monitor.get_probe_stats(name)
        assert stats["count"] == 1

    def test_stop_unknown_probe(self):
        """Ensure stopping a probe that was never started does not crash."""
        monitor = PerformanceMonitor()
        try:
            monitor.stop_probe("non_existent")
        except Exception as e:
            pytest.fail(f"stop_probe raised exception: {e}")

    def test_get_unknown_probe_stats(self):
        monitor = PerformanceMonitor()
        stats = monitor.get_probe_stats("unknown")
        assert stats == {}

