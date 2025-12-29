# Plan: Performance Benchmarking and Latency Optimization

## Phase 1: Instrumentation and Baserlining

- [ ] Task: Implement High-Resolution Telemetry Probes
    - [ ] Subtask: Write Tests for new telemetry methods in PerformanceMonitor.
    - [ ] Subtask: Implement start_probe(name) and stop_probe(name) using perf_counter_ns in utils/performance_monitor.py.
- [ ] Task: Instrument Core Hot Paths
    - [ ] Subtask: Add probes to capture_screen and process_frame in core/detection.py.
    - [ ] Subtask: Add probes to send_input in core/low_level_movement.py.
    - [ ] Subtask: Add probes to the main orchestration loop in main.py.
- [ ] Task: Establish Baseline Report
    - [ ] Subtask: Run the application in a controlled environment for 60 seconds.
    - [ ] Subtask: Generate a report of p50, p95, and p99 latency for each stage.

## Phase 2: Detection Loop Optimization

- [ ] Task: Optimize Image Buffer Handling
    - [ ] Subtask: Write Benchmarks for current mss + 
umpy conversion.
    - [ ] Subtask: Implement and verify strict zero-copy view creation.
- [ ] Task: Optimize Color Search Logic
    - [ ] Subtask: Write Benchmarks for cv2.inRange vs cv2.minMaxLoc on cropped regions.
    - [ ] Subtask: Refactor core/detection.py to use the fastest identified method for the specific ROI size.

## Phase 3: Input and Synchronization Optimization

- [ ] Task: Optimize Windows API Calls
    - [ ] Subtask: Write Tests for ctypes structure reuse.
    - [ ] Subtask: Refactor core/low_level_movement.py to pre-instantiate INPUT structures and cache user32 function pointers.
- [ ] Task: Implement Hybrid Busy-Wait Sync
    - [ ] Subtask: Write Tests for timing precision.
    - [ ] Subtask: Replace 	ime.sleep() in main.py with a hybrid sleep/spin-wait loop for precise frame pacing.

## Phase 4: Verification and Clean-up

- [ ] Task: Final Benchmarking
    - [ ] Subtask: Run the same 60-second test from Phase 1.
    - [ ] Subtask: Compare metrics against targets defined in spec.md.
- [ ] Task: Code Cleanup
    - [ ] Subtask: Remove temporary debugging probes (if any) or put them behind a feature flag.
    - [ ] Subtask: Ensure all tests pass and code complies with uff.
