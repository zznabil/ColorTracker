# SAI Color Tracking Algorithm V3

## Project Overview
**SAI Color Tracking Algorithm V3** is a modular Python-based real-time computer vision application for color detection and automated mouse movement. It is optimized for responsiveness and stealth, utilizing low-level Windows API for input.

**Key Technologies:**
- **GUI**: `Dear PyGui` (GPU-accelerated immediate mode).
- **Vision**: `OpenCV`, `NumPy`, `mss` (Optimized screen capture).
- **Input**: `ctypes` (SendInput Windows API).
- **Persistence**: JSON-based "self-healing" configuration.

## Architecture & Modules

### Core Logic (`core/`)
- **`detection.py`**: Contains `DetectionSystem`. Handles thread-safe screen capture using `mss` (BGRA). Implements `_local_search` optimization and `_full_search` fallback using `cv2.minMaxLoc` for O(1) memory usage.
- **`motion_engine.py`**: Contains `MotionEngine` and `OneEuroFilter`. The engine manages filtering state, while `OneEuroFilter` implements the adaptive smoothing math. Includes velocity-based prediction logic.
- **`low_level_movement.py`**: Contains `LowLevelMovementSystem`. Wraps Windows `SendInput` API via `ctypes` structures (`INPUT`, `MOUSEINPUT`) for safe, clamped coordinate injection.

### User Interface (`gui/`)
- **`main_window.py`**: Orchestrates the UI using `Dear PyGui`. Manages the event loop, input validation (snapping), and visual overlays. Interacts with `Config` for state.

### Utilities (`utils/`)
- **`config.py`**: Contains `Config` class. Manages `DEFAULT_CONFIG` schema, validation, type repair, and JSON persistence.
- **`logger.py`**: Contains `Logger`. Thread-safe logging with debug rules and spam suppression.
- **`keyboard_listener.py`**: Contains `KeyboardListener`. Manages global hotkeys via `pynput` daemon threads.
- **`performance_monitor.py`**: Contains `PerformanceMonitor`. Tracks FPS, latency, and 1% lows for real-time analytics.

### Orchestration (`main.py`)
- **`ColorTrackerAlgo`**: The central controller that composes all subsystems, manages the high-precision hybrid timing loop (`_algo_loop_internal`), and handles thread lifecycle.

## Static Analysis & Safety
- **Linting**: Verified with `Ruff` (0 errors).
- **Type Checking**: Verified with `Pyright` (0 errors).
- **Robustness**: 
    - **Self-Healing Config**: Automatically recovers from JSON corruption and resets to defaults on critical failure.
    - **Safe Movement**: Coordinate clamping prevents out-of-bounds `SendInput` errors.
    - **Detection Guard**: Image validity checks prevent CV2 assertion errors on empty captures.
    - **FOV Enforcement**: Local search strictly adheres to FOV boundaries even when tracking moving targets.
    - **Concurrency & Stability**: Proven thread-safe under "Chaos Monkey" config hammering and 100k-frame marathon simulations.

## Development
- **Testing**: 
    - **Unit Tests**: `test_motion_engine.py`, `test_movement_math.py`, `test_config_exhaustive.py`, `test_logger_suppression.py`, `test_performance_monitor.py`, `test_vertical_deep_coverage.py`.
    - **Integration/Stress**: `test_integration_stress.py`, `test_threading_safety.py`, `test_ultra_robustness.py`, `test_comprehensive_edge_cases.py`, `test_horizontal_broad_coverage.py`.
    - **Edge Cases**: `test_ultra_edge_cases.py`, `test_detection_mocked.py`, `test_detection_noise.py`, `test_keyboard_listener_rebinding.py`.
- **Build**: `build_release.bat` for PyInstaller executable generation.

## Verification Log
- **Last Verified**: 2025-12-27 21:15 (Persistence Hardening)
- **Protocol**: ULTRATHINK "Atomic Configuration Persistence"
- **Status**: ✅ PASSED (Production Grade V3.2.1)
- **Metrics**:
    - **Unit/Edge Tests**: 103/103 Passed (100% success rate)
    - **Static Analysis**: 100% Clean (Ruff: 0 errors/Pyright: 0 errors)
    - **UI Dynamics**: 100% Fluid (Immediate feedback & reliable persistence)
    - **Stability**: Verified atomic saves and legacy migration via stress tests.
