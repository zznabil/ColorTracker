import collections
import csv
import datetime
import json
import os
import threading
import time


class PerformanceMonitor:
    """
    Thread-safe performance monitoring utility.
    Tracks FPS, Frame Times, and Detection Latency.
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

    def record_frame(self, duration_sec: float, missed: bool = False):
        """
        Record the duration of a single logic loop frame.

        Args:
            duration_sec: Time taken for the frame in seconds.
            missed: Whether the frame missed its deadline.
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
            avg_frame = (sum(self.frame_times) / len(self.frame_times)) if self.frame_times else 0.0
            avg_detect = (sum(self.detection_times) / len(self.detection_times)) if self.detection_times else 0.0

            # 1% Lows calculation (99th percentile of frame time, converted to FPS)
            one_percent_low = 0.0
            if len(self.frame_times) > 100:
                sorted_times = sorted(self.frame_times, reverse=True)
                p99_index = int(len(sorted_times) * 0.01)
                p99_time_ms = sorted_times[p99_index]
                if p99_time_ms > 0:
                    one_percent_low = 1000.0 / p99_time_ms

            return {
                "fps": self.current_fps,
                "avg_frame_ms": avg_frame,
                "worst_frame_ms": self.worst_frame_time,
                "avg_detection_ms": avg_detect,
                "missed_frames": float(self.missed_frames),
                "one_percent_low_fps": one_percent_low
            }

    def get_history(self) -> dict[str, list[float]]:
        """Get historical data for plotting."""
        with self._lock:
            return {
                "fps": list(self.fps_history),
                "frame_times": list(self.frame_times),
                "detection_times": list(self.detection_times)
            }

    def reset_aggregates(self):
        """Reset max/min counters but keep history."""
        with self._lock:
            self.worst_frame_time = 0.0
            self.missed_frames = 0

    def export_history(self, filepath: str, format: str = "csv") -> bool:
        """
        Export performance history to a file.

        Args:
            filepath: Path to save the file.
            format: "csv" or "json".

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Ensure directory exists
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            data = self.get_history()

            # Prepare data with timestamp
            timestamp = datetime.datetime.now().isoformat()

            if format.lower() == "json":
                export_data = {
                    "timestamp": timestamp,
                    "stats": self.get_stats(),
                    "history": data
                }
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2)

            elif format.lower() == "csv":
                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)

                    # Write header with metadata
                    writer.writerow(["# SAI Color Tracker V3 Performance Export"])
                    writer.writerow([f"# Date: {timestamp}"])
                    stats = self.get_stats()
                    writer.writerow([f"# Average FPS: {stats['fps']:.2f}"])
                    writer.writerow([])

                    # Determine max length
                    max_len = max(
                        len(data["fps"]),
                        len(data["frame_times"]),
                        len(data["detection_times"])
                    )

                    writer.writerow(["Frame Index", "FPS", "Frame Time (ms)", "Detection Time (ms)"])

                    fps_list = list(data["fps"])
                    frame_times = list(data["frame_times"])
                    detection_times = list(data["detection_times"])

                    for i in range(max_len):
                        fps_val = fps_list[i] if i < len(fps_list) else ""
                        frame_val = frame_times[i] if i < len(frame_times) else ""
                        detect_val = detection_times[i] if i < len(detection_times) else ""
                        writer.writerow([i, fps_val, frame_val, detect_val])

            return True

        except Exception as e:
            print(f"Error exporting performance history: {e}")
            return False
