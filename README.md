# SAI Color Tracker V3

A high-performance, modular color tracking and mouse automation tool.

## Key Features
- Low-latency detection loop
- Multiple smoothing/prediction filters (EMA/DEMA/TEMA, etc.)
- Low-level Windows `SendInput` mouse movement
- DearPyGui-based GUI with optional HUD overlay

## Installation
1. Install Python 3.11+.
2. Install pip if it is missing:
   ```bash
   python -m ensurepip --upgrade
   ```
3. Install runtime dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

## Development
1. Install test dependencies:
   ```bash
   python -m pip install pytest
   ```
2. Run quality gates:
   ```bash
   ruff check .
   pyright .
   python -m pytest
   ```

## Usage
1. Run `python main.py`.
2. Select your target color in the Detection tab.
3. Use PageUp to start and PageDown to stop.

## Project Structure
- `core/`: Detection, prediction, and movement logic
- `gui/`: Main window layout and theme
- `utils/`: Config management, filters, and logging
- `docs/`: Manuals and guides

## Disclaimer
This software is intended for research and educational purposes only. Always use responsibly and adhere to the Terms of Service of any application you use this with.
