# SAI Color Tracker V3

A high-performance, modular color tracking and mouse automation tool.

## 🚀 Key Features
- **Low-Latency Detection**: <5ms latency using `cv2.minMaxLoc` (O(1) memory) and direct BGRA processing.
- **Unified Motion Engine**: 1 Euro Filter for jitter reduction + Velocity-based prediction (leads moving targets).
- **Stealth Input**: Uses low-level Windows `SendInput` API with coordinate clamping.
- **Real-Time HUD**: Visual FOV overlay for calibration and performance analytics.
- **Robust GUI**: Built with DearPyGui for minimal CPU impact and immediate visual feedback.

## 🛡 Safety & Stealth
- **Input Clamping**: All mouse coordinates are strictly clamped to screen boundaries (0-65535 absolute) to prevent invalid API calls.
- **Fail-Safes**: Global "Master Enable" switch instantly cuts all input signals.
- **Validation**: Configuration values are auto-repaired to safe ranges on load.
- **Stealth**: No "virtual mouse" drivers used; pure Windows API injection.

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
3. Configure **Motion Engine** settings (Stabilization/Responsiveness) in the Aim tab.
4. Use **PageUp** to Start and **PageDown** to Stop.
5. Press **F12** to toggle the debug console (requires `debug_mode` in config).

## 📁 Project Structure
- `core/`:
  - `detection.py`: MSS screen capture with local search optimization and zero-copy buffers.
  - `motion_engine.py`: 1 Euro Filter logic for adaptive smoothing and prediction.
  - `low_level_movement.py`: Direct input injection.
- `gui/`: Main window layout, theming, and overlay logic.
- `utils/`: Config management, logging, and performance monitoring.
- `docs/`: In-depth manuals and guides.

## ⚖️ Disclaimer
This software is intended for research and educational purposes only. Always use responsibly and adhere to the Terms of Service of any application you use this with.
