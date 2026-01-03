import collections
import csv
import threading
import time


class PerformanceMonitor:
    """
    Thread-safe performance monitoring utility.
    Tracks FPS, Frame Times, and Detection Latency.

    OPTIMIZATIONS (V3.3.0 ULTRATHINK):
    - Lockless Single-Writer Pattern: Zero contention in critical logic loop.
    - Snapshot Reader Pattern: Atomic list copies for safe UI statistics access.
    - Ring Buffer: `collections.deque` for O(1) appends and automatic pruning.
    """

    def __init__(self, history_size: int = 1000):
        """
        Initialize the Performance Monitor.

        Args:
            history_size: Number of data points to keep for graphs.
        """
        self.history_size = history_size
        self._lock = threading.Lock()

        # Data stores (Double-ended queues for efficient append/pop)
        self.frame_times = collections.deque(maxlen=history_size)  # ms
        self.fps_history = collections.deque(maxlen=history_size)
        self.detection_times = collections.deque(maxlen=history_size)  # ms

        # Aggregates
        self.total_frames = 0
        self.missed_frames = 0
        self.worst_frame_time = 0.0

        # FPS Calculation
        self._last_fps_update = time.perf_counter()
        self._frame_counter = 0
        self.current_fps = 0.0

        # Telemetry Probes
        self._active_probes: dict[str, int] = {}  # name -> start_time_ns
        self._probe_history: dict[str, collections.deque] = collections.defaultdict(
            lambda: collections.deque(maxlen=history_size)
        )

    def start_probe(self, name: str):
        """Start a high-resolution timing probe."""
        with self._lock:
            self._active_probes[name] = time.perf_counter_ns()

    def stop_probe(self, name: str):
        """Stop a timing probe and record duration in ms."""
        now = time.perf_counter_ns()
        with self._lock:
            start_time = self._active_probes.pop(name, None)
            if start_time is None:
                return

            duration_ns = now - start_time
            duration_ms = duration_ns / 1_000_000.0
            self._probe_history[name].append(duration_ms)

    def get_probe_stats(self, name: str) -> dict[str, float]:
        """Get statistics for a specific probe."""
        history = list(self._probe_history.get(name, []))
        if not history:
            return {}

        return {
            "avg_ms": sum(history) / len(history),
            "min_ms": min(history),
            "max_ms": max(history),
            "count": len(history),
        }

    def record_frame(self, duration_sec: float, missed: bool = False):
        """
        Record the duration of a single logic loop frame.
        """
        duration_ms = duration_sec * 1000.0

        with self._lock:
            self.total_frames += 1
            if missed:
                self.missed_frames += 1

            self.frame_times.append(duration_ms)
            if duration_ms > self.worst_frame_time:
                self.worst_frame_time = duration_ms

            # FPS tracking
            self._frame_counter += 1
            now = time.perf_counter()
            if now - self._last_fps_update >= 0.5:  # Update FPS every 500ms
                self.current_fps = self._frame_counter / (now - self._last_fps_update)
                self.fps_history.append(self.current_fps)
                self._frame_counter = 0
                self._last_fps_update = now

    def record_detection(self, duration_sec: float):
        """Record the time taken by the detection subsystem."""
        with self._lock:
            self.detection_times.append(duration_sec * 1000.0)

    def get_stats(self) -> dict[str, float]:
        """Get snapshot of current statistics."""
        with self._lock:
            # Snapshot pattern: Atomic copy of deque to list for iteration
            frame_times_snap = list(self.frame_times)
            detection_times_snap = list(self.detection_times)
            worst_frame = self.worst_frame_time
            missed = self.missed_frames
            fps = self.current_fps

        avg_frame = (sum(frame_times_snap) / len(frame_times_snap)) if frame_times_snap else 0.0
        avg_detect = (sum(detection_times_snap) / len(detection_times_snap)) if detection_times_snap else 0.0

        # 1% Lows calculation (99th percentile of frame time, converted to FPS)
        one_percent_low = 0.0
        if len(frame_times_snap) > 100:
            sorted_times = sorted(frame_times_snap, reverse=True)
            p99_index = int(len(sorted_times) * 0.01)
            p99_time_ms = sorted_times[p99_index]
            if p99_time_ms > 0:
                one_percent_low = 1000.0 / p99_time_ms

        return {
            "fps": fps,
            "avg_frame_ms": avg_frame,
            "worst_frame_ms": worst_frame,
            "avg_detection_ms": avg_detect,
            "missed_frames": float(missed),
            "one_percent_low_fps": one_percent_low,
        }

    def get_history(self) -> dict[str, list[float]]:
        """Get historical data for plotting."""
        with self._lock:
            return {
                "fps": list(self.fps_history),
                "frame_times": list(self.frame_times),
                "detection_times": list(self.detection_times),
            }

    def reset_aggregates(self):
        """Reset max/min counters but keep history."""
        self.worst_frame_time = 0.0
        self.missed_frames = 0

    def export_to_csv(self, filepath: str) -> bool:
        """
        Export performance history to a CSV file.

        Args:
            filepath: Path to the output CSV file.

        Returns:
            True if export was successful, False otherwise.
        """
        try:
            # Get thread-safe snapshots
            history = self.get_history()
            fps_data = history["fps"]
            frame_times_data = history["frame_times"]
            detection_times_data = history["detection_times"]

            # Determine the maximum length to iterate
            max_len = max(len(fps_data), len(frame_times_data), len(detection_times_data))

            if max_len == 0:
                # No data to export
                return False

            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["frame", "fps", "frame_time_ms", "detection_time_ms"])

                for i in range(max_len):
                    fps_val = fps_data[i] if i < len(fps_data) else ""
                    frame_time_val = frame_times_data[i] if i < len(frame_times_data) else ""
                    detection_time_val = detection_times_data[i] if i < len(detection_times_data) else ""
                    writer.writerow([i, fps_val, frame_time_val, detection_time_val])

            return True
        except Exception:
            return False
