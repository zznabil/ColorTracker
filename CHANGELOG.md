# Changelog - SAI Color Tracker Algorithm

All notable changes to this project will be documented in this file.

## [3.2.1] - 2025-12-27
### Added
- **Documented Configuration**: Root `config.json` now contains inline comments for every parameter.
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
