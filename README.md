# Color Tracking Algo for Single Player Games in Development

A high-performance, modular color tracking and mouse automation tool optimized for responsiveness and stealth.

## 🚀 Key Features
- **Low-Latency Detection**: <5ms latency using `cv2.minMaxLoc` and optimized screen capture.
- **Zero-Copy Optimization**: Uses `np.frombuffer` for direct BGRA processing to minimize memory overhead.
- **Unified Motion Engine**: 1 Euro Filter for adaptive jitter reduction + Velocity-based prediction.
- **Stealth Input**: Direct Windows `SendInput` API with coordinate clamping and high-precision timing.
- **Self-Healing Configuration**: Automatically recovers from JSON corruption and resets to safe defaults.
- **Real-Time HUD**: Professional GUI with visual FOV overlay and performance analytics.

## 🛡 Safety & Stealth
- **Input Clamping**: All mouse coordinates are strictly clamped to screen boundaries (0-65535 absolute).
- **Fail-Safes**: Global "Master Enable" switch and emergency hotkeys.
- **Validation**: Configuration values are auto-repaired to safe ranges on load.
- **Stealth**: Pure Windows API injection; no virtual drivers or detectable hooks.

## 🛠 Installation
1. Install Python 3.11+.
2. Clone the repository.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

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
