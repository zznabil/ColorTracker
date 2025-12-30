# Technology Stack

## Core Runtime
- **Language**: Python 3.12+ (Strict Mode)
- **Architecture**: 64-bit Windows

## Critical Libraries
| Component | Library | Purpose |
| :--- | :--- | :--- |
| **GUI** | `dearpygui` | GPU-accelerated Immediate Mode GUI (60+ FPS overlay) |
| **Vision** | `opencv-python` | `cv2.minMaxLoc`, `cv2.cvtColor` (Optimized C++ bindings) |
| **Capture** | `mss` | High-speed, thread-safe screen capture (DirectX/GDI) |
| **Math** | `numpy` | Zero-copy buffer views, vector arithmetic |
| **Input** | `ctypes` | Direct `user32.dll` / `SendInput` calls |

## Algorithmic Core
- **Smoothing**: **1 Euro Filter** (Adaptive Low-Pass Filter).
- **Prediction**: **Chebyshev Velocity Gating** ($v = \max(|dx|, |dy|)$).
- **Normalization**: **Pre-calculated Scaling** ($x_{norm} = x \cdot S_x$).
- **Timing**: **Hybrid Spin-Wait** (Sleep 90% -> Spin 10%).

## Quality Assurance
- **Linting**: `ruff` (Strict PEP 8).
- **Types**: `pyright` (Strict).
- **Tests**: `pytest` (Unit, Integration, Stress, Edge Cases).
- **Telemetry**: Custom `perf_counter_ns` probes (Lockless).

## V3.4.1 Updates

### Performance Monitor Perfection
- **Comprehensive Coverage**: Added `test_get_stats_comprehensive` for 1% Low FPS calculation logic.
- **Empty Probe Handling**: Added `TestProbeEmptyHistory` class for telemetry edge cases.
- **Passing Rate**: 100% (18/18 tests passing).

### Thread Safety Architecture
- **Sage/Artisan Separation**: Added `move_to_target()` delegation in `ColorTrackerAlgo` for proper thread isolation.
- **Hot-Path Caching**: Method reference hoisting in `_algo_loop_internal` eliminates redundant lookups.
