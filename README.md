# Color Tracking Algo for Single Player Games in Development - V3.2.3

A high-performance, modular color tracking and mouse automation tool optimized for responsiveness and stealth.

## 🚀 Key Features
- **Extreme Low-Latency Detection**: <2.5ms processing latency using cached FOV geometry and `cv2.minMaxLoc`.
- **Zero-Copy Memory Architecture**: Utilizes `np.frombuffer` for direct access to raw BGRA buffers.
- **Allocation-Free Input**: Reuses `ctypes.INPUT` structures in the low-level movement system to eliminate memory churn.
- **V3.2.3 Optimized Motion Engine**: 1 Euro Filter implementation with `__slots__`, inlined math, and FOV caching.
- **Adaptive Predictive Tracking**: Real-time velocity-based lookahead to overcome display lag and filter delay.
- **Direct Windows Input (Stealth)**: Low-level `SendInput` API calls with coordinate clamping for safe and undetectable interaction.
- **Self-Healing State Management**: Atomic JSON config persistence with automatic corruption recovery and type-repair.
- **Professional GUI & HUD**: GPU-accelerated Dear PyGui interface with real-time performance analytics (1% lows) and visual FOV overlays.
- **Surgical Performance Monitoring**: Clinical tracking of loop latency and frame-time consistency to ensure 960 FPS stability.

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
