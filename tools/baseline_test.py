#!/usr/bin/env python3
"""
Baseline Performance Test for ColorTracker

Runs application for 60 seconds and generates p50, p95, and p99 latency reports.
"""

import os
import statistics
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.detection import DetectionSystem
    from core.low_level_movement import LowLevelMovementSystem
    from core.motion_engine import MotionEngine
    from utils.config import Config
    from utils.performance_monitor import PerformanceMonitor
except ImportError as e:
    print(f"Failed to import all modules: {e}")
    sys.exit(1)


def run_baseline_test():
    """Run 60-second baseline test and generate latency statistics."""
    print("Starting 60-second baseline performance test...")
    print("This will test capture_screen, process_frame, and send_input probes.")

    # Initialize components
    config = Config()
    config.load()

    perf_monitor = PerformanceMonitor()
    detection = DetectionSystem(config, perf_monitor)
    motion_engine = MotionEngine(config)
    movement = LowLevelMovementSystem(config, perf_monitor)

    # Mock a simple target for detection
    config.target_color = 0xFF0000  # Red
    config.color_tolerance = 10
    config.enabled = True

    # Test parameters
    test_duration = 60.0  # seconds
    frame_interval = 1.0 / 1000.0  # 1000 FPS for stress testing

    print(f"Running {test_duration}s stress test at 1000 FPS...")
    print("Collecting telemetry data...")

    start_time = time.perf_counter()
    frame_count = 0

    try:
        while True:
            loop_start = time.perf_counter()

            # Test detection capture
            found, x, y = detection.find_target()

            # Test motion processing if target found
            if found:
                predicted_x, predicted_y = motion_engine.process(x, y, 1.0 / 1000.0)
                movement.move_to_target(predicted_x, predicted_y)

            # Record frame time
            loop_end = time.perf_counter()
            actual_frame_time = loop_end - loop_start
            perf_monitor.record_frame(actual_frame_time, missed=False)

            frame_count += 1

            # Check if test duration reached
            if loop_end - start_time >= test_duration:
                break

            # Calculate sleep time
            sleep_time = frame_interval - actual_frame_time
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")

    finally:
        total_time = time.perf_counter() - start_time

        print("\nBaseline Test Complete!")
        print(f"Total Duration: {total_time:.2f}s")
        print(f"Frames Processed: {frame_count}")
        print(f"Average FPS: {frame_count / total_time:.1f}")

        # Generate detailed probe statistics
        print("\n=== PROBE STATISTICS ===")

        capture_stats = perf_monitor.get_probe_stats("detection_capture")
        if capture_stats:
            print("detection_capture:")
            print(f"  Average: {capture_stats['avg_ms']:.3f}ms")
            print(f"  Min: {capture_stats['min_ms']:.3f}ms")
            print(f"  Max: {capture_stats['max_ms']:.3f}ms")
            print(f"  Count: {capture_stats['count']}")

        process_stats = perf_monitor.get_probe_stats("detection_process")
        if process_stats:
            print("detection_process:")
            print(f"  Average: {process_stats['avg_ms']:.3f}ms")
            print(f"  Min: {process_stats['min_ms']:.3f}ms")
            print(f"  Max: {process_stats['max_ms']:.3f}ms")
            print(f"  Count: {process_stats['count']}")

        input_stats = perf_monitor.get_probe_stats("movement_input")
        if input_stats:
            print("movement_input:")
            print(f"  Average: {input_stats['avg_ms']:.3f}ms")
            print(f"  Min: {input_stats['min_ms']:.3f}ms")
            print(f"  Max: {input_stats['max_ms']:.3f}ms")
            print(f"  Count: {input_stats['count']}")

        orchestration_stats = perf_monitor.get_probe_stats("main_loop_active")
        if orchestration_stats:
            print("main_loop_active:")
            print(f"  Average: {orchestration_stats['avg_ms']:.3f}ms")
            print(f"  Min: {orchestration_stats['min_ms']:.3f}ms")
            print(f"  Max: {orchestration_stats['max_ms']:.3f}ms")
            print(f"  Count: {orchestration_stats['count']}")

        # Calculate percentiles from frame times
        frame_times = list(perf_monitor.frame_times) if hasattr(perf_monitor, "frame_times") else []
        if frame_times:
            p50 = statistics.quantiles(frame_times, n=2)[0] * 1000  # Convert to ms
            p95 = statistics.quantiles(frame_times, n=20)[18] * 1000  # 95th percentile
            p99 = statistics.quantiles(frame_times, n=100)[98] * 1000  # 99th percentile

            print("\n=== FRAME TIME PERCENTILES ===")
            print(f"50th percentile (p50): {p50:.3f}ms")
            print(f"95th percentile (p95): {p95:.3f}ms")
            print(f"99th percentile (p99): {p99:.3f}ms")

            print("\n=== TARGET ANALYSIS ===")
            print("Detection Latency Target: < 2.0ms")
            print("Input Injection Target: < 0.1ms")
            print("Jitter Target: ± 0.1ms")

            if process_stats:
                avg_detection = process_stats["avg_ms"]
                if avg_detection < 2.0:
                    print(f"✅ Detection: ACHIEVED ({avg_detection:.3f}ms < 2.0ms)")
                else:
                    print(f"❌ Detection: NOT ACHIEVED ({avg_detection:.3f}ms ≥ 2.0ms)")

            if input_stats:
                avg_input = input_stats["avg_ms"]
                if avg_input < 0.1:
                    print(f"✅ Input: ACHIEVED ({avg_input:.3f}ms < 0.1ms)")
                else:
                    print(f"❌ Input: NOT ACHIEVED ({avg_input:.3f}ms ≥ 0.1ms)")

            # Calculate jitter (standard deviation of frame times)
            if len(frame_times) > 1:
                frame_std = statistics.stdev(frame_times) * 1000  # Convert to ms
                if frame_std <= 0.1:
                    print(f"✅ Jitter: ACHIEVED ({frame_std:.3f}ms ≤ 0.1ms)")
                else:
                    print(f"❌ Jitter: NOT ACHIEVED ({frame_std:.3f}ms > 0.1ms)")


if __name__ == "__main__":
    run_baseline_test()
