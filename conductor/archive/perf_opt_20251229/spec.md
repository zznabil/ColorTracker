# Specification: Performance Benchmarking and Latency Optimization

## 1. Objective
Reduce the end-to-end latency of the color tracking loop to < 2.5ms (99th percentile) and eliminate non-deterministic GC pauses or lock contention in the hot path.

## 2. Scope
- **Target Modules:**
    - core/detection.py: Image capture (MSS) and processing (OpenCV).
    - core/low_level_movement.py: Input injection (SendInput).
    - main.py: Main loop orchestration and synchronization.
- **Out of Scope:**
    - GUI rendering optimization (Dear PyGui is already on a separate thread).
    - Network latency (local processing only).

## 3. Key Metrics
| Metric | Current Estimate | Target |
| :--- | :--- | :--- |
| **Detection Latency** | ~3-5ms | < 2.0ms |
| **Input Injection Overhead** | ~0.5ms | < 0.1ms |
| **Jitter (Loop Variance)** | +/- 1ms | +/- 0.1ms |

## 4. Implementation Strategy
1.  **Instrumentation:** Integrate 	ime.perf_counter_ns() probes into the PerformanceMonitor to capture microsecond-level timing of distinct loop phases.
2.  **Detection Optimization:**
    - Verify zero-copy behavior of 
p.frombuffer.
    - Explore cv2.UMat (Transparent API) if GPU offload is viable without PCI-e transfer penalty.
    - Optimize FOV cropping logic to avoid slice copying.
3.  **Movement Optimization:**
    - Cache ctypes interfaces and structures to avoid initialization overhead per call.
    - Use QueryPerformanceCounter for busy-wait loops instead of 	ime.sleep for sub-millisecond precision.
4.  **Memory Management:**
    - Audit the hot loop for object allocations (using 	racemalloc).
    - Pre-allocate all reusable buffers and objects.

## 5. Constraints
- Must maintain thread safety with the GUI thread.
- Must not compromise the "Human-Like" movement characteristics (no robotic snapping).
