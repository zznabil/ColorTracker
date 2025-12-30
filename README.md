# Color Tracking Algo for Single Player Games in Development - V3.4.1

A high-performance, modular color tracking and mouse automation tool optimized for responsiveness and stealth.

## 🚀 Key Features
- **Extreme Low-Latency Detection**: <2.5ms processing latency via cached FOV geometry and O(1) `cv2.minMaxLoc`.
- **Zero-Copy Memory Architecture**: Direct hardware buffer access via `np.frombuffer` views.
- **High-Resolution Telemetry**: Custom microsecond-level tracing of hot paths (`start_probe`/`stop_probe`) for performance auditing.
- **Lockless Telemetry**: Single-writer/snapshot-reader pattern for zero-contention performance monitoring.
- **Config Versioning**: Observer pattern with O(1) version checks to eliminate redundant hot-path logic.
- **Optimized Orchestration**: Method reference caching and config hot-reload throttling for peak loop throughput.
- **Chebyshev Velocity Gating**: Advanced prediction logic (`max(abs(dx), abs(dy))`) ensuring responsive tracking for vertical movement.
- **Allocation-Free Input**: C-structure reuse, function pointer caching, and pre-calculated coordinate scaling in `low_level_movement` ($O(0)$ allocation).
- **Precision Hybrid Sync**: Fused `time.sleep` and micro-spin-wait for nanosecond timing accuracy without CPU pinning.
- **Self-Healing State Management**: Atomic JSON config persistence with automatic corruption recovery and type-repair.
- **Professional HUD**: GPU-accelerated Dear PyGui interface with real-time 1% low analytics and visual overlays.
- **Thread-Safe Delegation**: `ColorTrackerAlgo.move_to_target()` ensures proper Sage/Artisan separation and thread safety.

## 🏛 Architectural Archetypes
This project follows a strict structural duality to maintain clinical precision:
- **Archetype A: The Sage (Logic/Data)**: The `core/` and `utils/` layers. Focused on type-safety, O(1) memory allocation, and deterministic execution.
- **Archetype B: The Artisan (Visual/Physics)**: The `gui/` layer. Focused on aesthetic excellence, responsive human-computer interaction, and motion physics.

## 🛡 Safety & Stealth
- **Input Clamping**: All mouse coordinates are strictly clamped to screen boundaries (0-65535 absolute).
- **Fail-Safes**: Global "Master Enable" switch and emergency hotkeys.
- **Validation**: Configuration values are auto-repaired to safe ranges on load.
- **Stealth**: Pure Windows API injection; no virtual drivers or detectable hooks.

## 🛠 Installation
1. **Zero to Hero (Recommended)**:
    Right-click `setup_and_run.ps1` and select "Run with PowerShell". This automates Python installation, virtual environment setup, dependency management, and build.

2. **Manual Installation**:
    - Install Python 3.12+.
    - Clone repository.
    - Install dependencies: `pip install -r requirements.txt`

## 🎮 Usage
1. Run `python main.py`.
2. Select your **Target Color** in the Detection tab.
3. Configure **Motion Engine** settings (min_cutoff/beta) in the Aim tab.
4. Use **PageUp** to **Start Tracking** and **PageDown** to **Stop Tracking**.
5. Press **F12** to toggle the debug console (requires `debug_mode` enabled).

## 📁 Project Structure
- `core/`:
  - `detection.py`: Optimized screen capture with local search and zero-copy buffers.
  - `motion_engine.py`: 1 Euro Filter logic and velocity-based prediction.
  - `low_level_movement.py`: Direct Windows API input injection with thread-safe delegation.
- `gui/`:
  - Dear PyGui layout, theming, and real-time overlay logic.
- `utils/`:
  - Config persistence, thread-safe logging, and performance monitoring with comprehensive test coverage.
- `docs/`:
  - In-depth manuals, user guides, and [Technical Architecture Walkthrough](docs/TECHNICAL_WALKTHROUGH.md).
- `tests/`:
  - Comprehensive test suite covering unit, integration, edge cases, and ultra-robustness scenarios.

## ⚖️ Disclaimer
This software is intended for research and educational purposes only. Always use responsibly and adhere to Terms of Service of any application you use this with.

## 🏆 V3.4.1 Updates (2025-12-30)
### Core Integrity Fixes
- **Performance Monitor Perfection**: Fixed critical failures in `tests/test_performance_monitor.py` and added comprehensive 1% Low FPS calculation coverage.
- **Thread Safety Restoration**: Added `move_to_target()` delegation method in `ColorTrackerAlgo` ensuring proper Sage/Artisan thread separation.
- **Benchmark Module Resolution**: Fixed `benchmark.py` import mocking to support headless performance auditing.

### Test Coverage
- **All Tests Passing**: 128/128 tests (100% integrity) confirming system stability.
- **New Test Suites**: Added `TestProbeEmptyHistory` class for empty probe edge cases.
- **Updated Tests**: Fixed `test_horizontal_broad_coverage.py` to align with stealth protocol (absolute coordinate usage).

### SINGULARITY & ULTRATHINK Alignment
The entire codebase now enforces strict "ULTRATHINK" optimizations for V3.4.1+:
1. **GC Management**: `gc.disable()` in hot loops. Manual `gc.collect(1)` every 600 frames.
2. **Hybrid Sync**: `_smart_sleep` combines bulk wait + spin with `timeBeginPeriod(1)`.
3. **Zero-Copy Vision**: `np.frombuffer` on `mss` shots. Avoid `np.array()` copies.
4. **Math Inlining**: Pre-calculate constants (e.g., coordinate scaling) to avoid division.
5. **Memory Identity**: Verify structure reuse via `assert obj1 is obj2` in tests.
