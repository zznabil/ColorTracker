# Color Tracking Algo for Single Player Games in Development - V3.5.1

![Version](https://img.shields.io/badge/version-3.5.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-windows-lightgrey.svg)

A high-performance, hardened, modular color tracking and mouse automation tool optimized for responsiveness, stealth, and stability.

## 🚀 Key Features
- **Extreme Low-Latency Detection**: <2.5ms processing latency via cached FOV geometry and O(1) `cv2.minMaxLoc`.
- **Hardened Resource Safety**: Leak-proof GDI and Clipboard management via strict "Policeman Protocol" compliance.
- **Stealth Mode (WDA)**: Integrated `SetWindowDisplayAffinity` to evade screen capture (OBS, Discord, etc.).
- **Dynamic Keybinding**: Instant hotkey updates without restart via thread-safe listener registry.
- **Thread-Safe Telemetry**: Atomic performance monitoring and logging for zero-contention diagnostics.
- **Chebyshev Velocity Gating**: Max(dx, dy) speed estimation to eliminate vertical prediction deadzone.
- **Predictive Stability Logic**: Deceleration dampening and direction-flip suppression for precise tracking.
- **Adaptive Clamping**: Proximity-based damping to prevent overshooting near targets.
- **Smart Sleep (Hybrid Sync)**: Fused `time.sleep` and micro-spin-wait for nanosecond timing accuracy.
- **Self-Healing State Management**: Atomic JSON config persistence with automatic corruption recovery.
- **Professional HUD**: GPU-accelerated Dear PyGui interface with pulsing status and 1% low analytics.

- **Precision Picker System**: Advanced color selection featuring Global Magnifier for desktop-wide pixel access, Pixel-Perfect Navigation with arrow key controls, and Precision Lens visuals with circular viewport, crosshair overlay, and real-time HEX/RGB/XY telemetry.
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
   - Clone the repository.
   - Install dependencies: `pip install -r requirements.txt`

## 🎮 Usage
1. Run `python main.py`.
2. Select your **Target Color** in the VISION tab.
3. Configure **Motion Engine** settings (min_cutoff/beta) in the COMBAT tab.
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
