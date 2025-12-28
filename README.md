# Color Tracking Algo for Single Player Games in Development - V3.3.0

A high-performance, modular color tracking and mouse automation tool optimized for responsiveness and stealth.

## 🚀 Key Features
- **Extreme Low-Latency Detection**: <2.5ms processing latency via cached FOV geometry and O(1) `cv2.minMaxLoc`.
- **Zero-Copy Memory Architecture**: Direct hardware buffer access via `np.frombuffer` views.
- **Lockless Telemetry**: Single-writer/snapshot-reader pattern for zero-contention performance monitoring.
- **Config Versioning**: Observer pattern with O(1) version checks to eliminate redundant hot-path logic.
- **Optimized Orchestration**: Method reference caching and config hot-reload throttling for peak loop throughput.
- **Allocation-Free Input**: C-structure reuse in `low_level_movement` to eliminate memory churn ($O(0)$ allocation).
- **Hybrid Precision Sync**: Fused `time.sleep` and micro-spin-wait for nanosecond timing accuracy without CPU pinning.
- **Self-Healing State Management**: Atomic JSON config persistence with automatic corruption recovery and type-repair.
- **Professional HUD**: GPU-accelerated Dear PyGui interface with real-time 1% low analytics and visual overlays.

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
   - Install Python 3.11+.
   - Clone the repository.
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
  - `low_level_movement.py`: Direct Windows API input injection.
- `gui/`: `DearPyGui` layout, theming, and real-time overlay logic.
- `utils/`: Config persistence, thread-safe logging, and performance monitoring.
- `docs/`: In-depth manuals and user guides.

## ⚖️ Disclaimer
This software is intended for research and educational purposes only. Always use responsibly and adhere to the Terms of Service of any application you use this with.
