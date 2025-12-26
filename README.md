# SAI Color Tracker V3

A high-performance, modular color tracking and mouse automation tool.

## 🚀 Key Features
- **Low-Latency Detection**: <5ms average capture-to-process time.
- **Advanced Filtering**: DEMA/TEMA/Dynamic filters for smooth, human-like prediction.
- **Stealth Input**: Uses low-level Windows `SendInput` API.
- **Real-Time HUD**: Visual FOV overlay for calibration.
- **Robust GUI**: Built with DearPyGui for minimal CPU impact.

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
3. Use **PageUp** to Start and **PageDown** to Stop.
4. Press **F12** to toggle the debug console.

## 📁 Project Structure
- `core/`: Detection, Prediction, and Movement logic.
- `gui/`: Main window layout and theme.
- `utils/`: Config management, filters, and logging.
- `docs/`: In-depth manuals and guides.

## ⚖️ Disclaimer
This software is intended for research and educational purposes only. Always use responsibly and adhere to the Terms of Service of any application you use this with.
