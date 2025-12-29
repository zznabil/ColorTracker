# Plan: Performance Benchmarking and Latency Optimization

## Phase 1: Instrumentation and Baserlining [checkpoint: d143e65]

- [x] Task: Implement High-Resolution Telemetry Probes [dee1527]
    - [ ] Subtask: Write Tests for new telemetry methods in PerformanceMonitor.
    - [ ] Subtask: Implement start_probe(name) and stop_probe(name) using perf_counter_ns in utils/performance_monitor.py.
- [x] Task: Instrument Core Hot Paths [5fbb84f]
    - [ ] Subtask: Add probes to capture_screen and process_frame in core/detection.py.
    - [ ] Subtask: Add probes to send_input in core/low_level_movement.py.
    - [ ] Subtask: Add probes to the main orchestration loop in main.py.
- [x] Task: Establish Baseline Report [6d09f00]
    - [ ] Subtask: Run the application in a controlled environment for 60 seconds.
    - [ ] Subtask: Generate a report of p50, p95, and p99 latency for each stage.

## Phase 2: Detection Loop Optimization [checkpoint: 6a8d367]

- [x] Task: Optimize Image Buffer Handling [934b32d]
    - [ ] Subtask: Write Benchmarks for current mss + 
umpy conversion.
    - [ ] Subtask: Implement and verify strict zero-copy view creation.
- [x] Task: Optimize Color Search Logic [420e79d]
    - [ ] Subtask: Write Benchmarks for cv2.inRange vs cv2.minMaxLoc on cropped regions.
    - [ ] Subtask: Refactor core/detection.py to use the fastest identified method for the specific ROI size.

## Phase 3: Input and Synchronization Optimization [checkpoint: 58a438b]

- [x] Task: Optimize Windows API Calls [2f2a8dc]
    - [ ] Subtask: Write Tests for ctypes structure reuse.
    - [ ] Subtask: Refactor core/low_level_movement.py to pre-instantiate INPUT structures and cache user32 function pointers.
- [x] Task: Implement Hybrid Busy-Wait Sync [da8cd67]
    - [ ] Subtask: Write Tests for timing precision.
    - [ ] Subtask: Replace 	ime.sleep() in main.py with a hybrid sleep/spin-wait loop for precise frame pacing.

## Phase 4: Verification and Clean-up

- [x] Task: Final Benchmarking [588a70f]
    - [ ] Subtask: Run the same 60-second test from Phase 1.
    - [ ] Subtask: Compare metrics against targets defined in spec.md.
- [x] Task: Code Cleanup [d34d583]
    - [ ] Subtask: Remove temporary debugging probes (if any) or put them behind a feature flag.
    - [ ] Subtask: Ensure all tests pass and code complies with 
uff.
