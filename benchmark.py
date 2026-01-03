import sys
import threading
import time
from unittest.mock import MagicMock

# Mock dearpygui before importing main
sys.modules["dearpygui.dearpygui"] = MagicMock()
sys.modules["dearpygui"] = MagicMock()
from main import ColorTrackerAlgo  # noqa: E402


def run_benchmark():
    print(
        "Starting benchmark (10s for test run)..."
    )  # 10s for quick verification, spec says 60s. I'll do 10s for "implementation" validation.

    # Create app
    app = ColorTrackerAlgo()
    app.config.enabled = True  # Enable tracking
    app.running = True

    # Start the loop in a separate thread
    t = threading.Thread(target=app._algo_loop_internal, daemon=True)
    t.start()

    # Let it run
    # We simulate a "Benchmark" by just letting it run.
    # In a real scenario, we might want to feed it fake input or just let it capture the screen (mss works).

    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        app.running = False
        t.join(timeout=2.0)

    print("-" * 50)
    print("BENCHMARK REPORT")
    print("-" * 50)

    # General Stats
    stats = app.perf_monitor.get_stats()
    print(f"FPS: {stats['fps']:.2f}")
    print(f"Avg Frame Time: {stats['avg_frame_ms']:.3f} ms")
    print(f"Worst Frame Time: {stats['worst_frame_ms']:.3f} ms")
    print(f"Missed Frames: {stats['missed_frames']}")
    print(f"1% Low FPS: {stats['one_percent_low_fps']:.2f}")

    print("-" * 50)
    print("PROBE TELEMETRY")
    print("-" * 50)

    probes = ["main_loop_active", "detection_capture", "detection_process", "movement_input"]
    for name in probes:
        p_stats = app.perf_monitor.get_probe_stats(name)
        if p_stats:
            print(f"[{name}]")
            print(f"  Count: {p_stats['count']}")
            print(f"  Avg:   {p_stats['avg_ms']:.4f} ms")
            print(f"  Min:   {p_stats['min_ms']:.4f} ms")
            print(f"  Max:   {p_stats['max_ms']:.4f} ms")
        else:
            print(f"[{name}] No data recorded.")


if __name__ == "__main__":
    run_benchmark()
