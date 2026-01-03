# Changelog - SAI Color Tracker Algorithm

All notable changes to this project will be documented in this file.

## [3.5.1] - 2026-01-03
### Added (Hardening & QoL)
- **Stealth Mode**: Implemented `SetWindowDisplayAffinity` (WDA_EXCLUDEFROMCAPTURE) to hide the GUI from screen capture software (OBS, Discord).
- **Dynamic Hotkey Rebinding**: Enabled instant hotkey updates without application restart by refactoring the `KeyboardListener` registry.
- **Pulsing Status Indicator**: Added dynamic alpha-modulated pulsing for the "ACTIVE" status indicator to provide better visual feedback.
- **DPI Awareness Logging**: Integrated system DPI scale factor reporting during initialization for improved coordinate troubleshooting.

### Fixed (Stability & Resources)
- **GDI Resource Safety**: Fixed a critical Device Context (DC) leak in the color picker by wrapping GDI calls in `try...finally` blocks.
- **Clipboard Hardening**: Refactored clipboard interaction with robust Win32 memory management (`GlobalLock`/`GlobalFree`) and error handling.
- **Threading Safety**: Eliminated race conditions by implementing `threading.Lock` across `running` state, `Logger` buffers, `PerformanceMonitor` telemetry, and `KeyboardListener` callbacks.
- **Motion Stability**: Resolved numerical "spikes" at extreme frame rates (>1000 FPS) and fixed a logic bug in direction-flip suppression.
- **GUI Crash**: Fixed a `SystemError` caused by an unsupported `width` parameter in `dpg.add_text`.
- **FOV Persistence**: Resolved a state-sync issue where FOV overlay visibility would reset to default on launch.

### Quality
- **Packaging**: Modernized project structure with `pyproject.toml` and updated `requirements.txt` to current library versions (DearPyGui 2.1.1, MSS 10.1.0).
- **Documentation**: Updated badges, version references, and setup scripts to align with Python 3.12+ requirements.
- Cleaned up `ruff` linting violations and optimized hot-path logging using `hash()` instead of `md5`.
- Removed ghost `nul` file and identified dead code in `gui/color_picker.py`.

## [3.5.0] - 2026-01-02
### Added (Precision Lens UI Overhaul)
- **Precision Lens Magnifier**: Redesigned magnifier as a circular viewport with crosshair overlay and dynamic data pill displaying real-time telemetry (HEX, RGB, XY coordinates).
- **Adaptive Clamping**: Implemented proximity-based damping in `MotionEngine` to prevent overshooting near targets.
- **Velocity Standardization**: Renamed all "speed" references to "velocity" for consistency across the codebase.

### Refactored (Architecture)
- **Systems First Initialization**: Refactored `main.py` to initialize core systems (detection, motion, input) before GUI launch for improved startup performance and error handling.

## [3.4.1] - 2026-01-02
### Added (Precision Picker)
- **Global Magnifier**: Implemented viewport transformation logic to allow the color picker to track pixels outside the main window boundaries (Desktop, Taskbar, etc.).
- **Pixel-Perfect Navigation**: Added Arrow Key support (Up/Down/Left/Right) for precise 1px cursor movement during picking mode.
- **Enhanced Visuals**: 
  - Integrated manual Nearest-Neighbor upscaling via NumPy for crisp 14x14 pixel blocks.
  - Added high-contrast center highlight and pixel grid overlay.
- **Real-Time Telemetry**: Magnifier now displays live HEX, RGB, and XY coordinates.
- **Color Accuracy**: Refactored `_update_picking_logic` to use NumPy for mathematically correct BGR->RGB conversion, eliminating channel swapping bugs.

### Added (Harmony Merge)
- **Predictive Stability Enhancements**: Implemented **Deceleration Dampening**, **Direction-Flip Logic**, and **Distance Clamping** (150px) in `MotionEngine` to eliminate high-scale prediction overshooting.
- **Chebyshev Velocity Gating**: Injected `max(abs(dx), abs(dy))` speed estimation in `MotionEngine` to fix the vertical prediction deadzone bug.
- **Scaling Optimization**: Replaced division with pre-calculated multiplication (`_x_scale` / `_y_scale`) in the 1000Hz `move_mouse_absolute` loop.
- **Zero-Copy Buffer Management**: Direct `np.frombuffer` access to BGRA memory in `DetectionSystem` for allocation-free capture.
- **Thread-Local MSS Isolation**: Implemented `threading.local()` for MSS instances to ensure lock-free concurrency.
- **DLL Caching**: Cached Windows API function pointers in `LowLevelMovementSystem` to eliminate repeated DLL lookups.
- **Smart Sleep Orchestrator**: Hybrid timing loop with `time.sleep` and micro-spin-wait for nanosecond frame pacing.
- **Telemetry Probes**: High-resolution microsecond tracing (`start_probe`/`stop_probe`) for performance auditing.
- **Verification Suites**: Harmonized `test_vertical_prediction.py` and `test_low_level_movement_optimization.py` into the main test gate.
- **Documentation Overhaul**: Updated all .md files (README, User Guide, UI Plan) to reflect V3.4.1 state and actual GUI structure.

## [3.4.0] - 2025-12-29
### Added (Observability)
- **High-Resolution Telemetry**: Implemented `perf_counter_ns` probes in `PerformanceMonitor` for microsecond-level tracing of detection, capture, and input phases.
- **Benchmarking Suite**: Introduced a comprehensive suite of benchmarking tools in `tools/` for automated performance regression testing.
- **Precision Hybrid Sync**: Refactored main loop timing into a `_smart_sleep` orchestrator, utilizing sub-millisecond spin-waiting for nanosecond frame pacing.

### Optimized (Performance)
- **MSS Capture Acceleration**: Disabled cursor capture in `mss` instance to reduce OS-level capture latency (~25% speedup).
- **Windows API Caching**: Cached `SendInput` function pointers in `LowLevelMovementSystem` to eliminate repeated DLL symbol lookups in the hot path.
- **Allocation Pruning**: Pre-allocated capture area dictionaries in `DetectionSystem` to achieve zero-allocation search cycles.

## [3.3.1] - 2025-12-29
### Added (Ironclad)
- **Strict Type Safety**: Enforced Python 3.12+ compliance with `pyright` strict mode enabled (0 errors).
- **Runtime Robustness**: Hardened `Logger` to handle missing `stderr` streams, preventing crashes in frozen/GUI-only environments.

## [3.3.0] - 2025-12-28
### Added (Titanium)
- **Lockless Telemetry**: Re-engineered `PerformanceMonitor` to use a transactional snapshot-reader pattern, eliminating lock contention in the high-frequency logic loop.
- **Config Versioning (Observer Pattern)**: Integrated an O(1) version integer in `Config` via `__setattr__` override. Subsystems now skip redundant cache invalidation unless the configuration actually changes.
- **Local Variable Caching**: Explicitly hoisted critical attributes (`self.config.enabled`, etc.) to local scope in `main.py` and `core/detection.py` to bypass Python's object dictionary lookup overhead.
- **Viewport Expansion**: Resized main UI to 480x730 to accommodate advanced telemetry and future analytics panes.

## [3.2.3] - 2025-12-28
### Optimized (Gem Harvest)
- **FOV Caching**: Implemented `_update_fov_cache` in detection system to reduce hot-path overhead.
- **Input Structure Reuse**: Cached `ctypes.INPUT` structures in low-level movement system to prevent allocation churn.
### Added
- **Optimization Tests**: Added dedicated test suite for low-level movement performance integrity.
- **Motion Engine Recalibration**: 
  - Validated scientific ranges for `beta` (0.0001-0.1) and `min_cutoff` (0.01-5.0).
  - Resolved "imperceptible stabilization" issue by preventing Nyquist frequency violations.
- **Limit Expansion (User Requested)**:
  - Unlocked `min_cutoff` up to **25.0** for raw-like input feel.
  - Expanded `beta` to **0.3** (Safety Capped) with 0.001 precision snapping.

## [3.2.2] - 2025-12-28
### Added
- **Architectural Overhaul**: Formalized Archetype A (The Sage) and Archetype B (The Artisan) design patterns in documentation.
- **Zero to Hero Guide**: Added `docs/setup.md` for automated PowerShell deployment.
- **Low-Level Specifications**: Documented `__slots__` and mathematical inlining performance gains.

## [3.2.1] - 2025-12-27
### Added
- **Documented Configuration**: Root `config.json` now contains inline comments for every parameter.
- **Improved FOV Control**:
  - Reduced FOV lower limit from 25 to 5 for experimental ultra-local tracking.
  - Implemented 5-unit incremental snapping for granular detection area tuning.
- **New Task Management**: Integrated `taskmaster` for granular development tracking.

### Optimized
- **OneEuroFilter Performance**:
  - Implemented `__slots__` to reduce object memory footprint and speed up attribute access.
  - Inlined math operations within `__call__` to eliminate method call overhead for `smoothing_factor` and `exponential_smoothing` in the high-frequency tracking loop.
- **Resource Cleanup**: Automated removal of legacy session branches.

## [3.2.0] - 2025-12-27
### Added
- **Zero-Copy Capture**: Implemented `np.frombuffer` in `DetectionSystem` to process BGRA buffers directly from screen memory.
- **Local Search Enhancement**: Added FOV enforcement within local search to prevent targets from being tracked outside defined boundaries.
- **Coordinate Clamping**: Integrated strict safety clamping in `MotionEngine` to prevent Windows API out-of-bounds errors.

### Fixed
- **MagicMock Poisoning**: Resolved issue where test mocks could poison configuration float values.
- **Timing Logic**: Refactored `MotionEngine` to use deterministic `dt`-based time advancement for test reliability.

## [3.1.0] - Earlier 2025-12
### Added
- **Dear PyGui Integration**: Transitioned to a GPU-accelerated immediate mode GUI.
- **Real-Time Analytics**: Added FPS monitoring and 1% low calculations.
- **Self-Healing Config**: Implemented robust JSON validation and auto-repair logic.

## [3.0.0] - Initial V3 Release
- Full rewrite of core logic for modularity and performance.
- Implementation of the 1 Euro Filter algorithm.
- Direct `SendInput` Windows API integration.
