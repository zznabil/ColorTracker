# Changelog - SAI Color Tracker Algorithm

All notable changes to this project will be documented in this file.

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
