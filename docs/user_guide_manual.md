# SAI Color Tracking Algorithm V3 - User Guide

## Introduction
The SAI Color Tracking Algorithm V3 is a color detection and tracking tool. It detects a target color on screen and moves the mouse cursor toward the detected target.

## Features
- Fast detection loop using `mss`
- Predictive tracking with multiple filter options
- Adjustable smoothing to mimic natural mouse movement
- Overlay HUD for FOV visualization
- Self-healing configuration

## Installation
1. Prerequisites:
   - Windows 10/11
   - Python 3.11+
2. Install pip if it is missing:
   ```bash
   python -m ensurepip --upgrade
   ```
3. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
4. Run:
   ```bash
   python main.py
   ```

## Filter Methods Explained
The tracking system uses various exponential moving average (EMA) filters for prediction and smoothing. The `smoothing` parameter controls filter behavior:

- **EMA (Exponential Moving Average)**: Standard smoothing filter. Uses alpha = 1.0 / (smoothing + 1.0). Higher smoothing = slower response.

- **DEMA (Double EMA)**: Two-layer EMA that reduces lag. Formula: 2*EMA1 - EMA2(EMA1). Faster than EMA with similar smoothness.

- **TEMA (Triple EMA)**: Three-layer EMA with minimal lag. Formula: 3*EMA1 - 3*EMA2 + EMA3. Fastest EMA variant.

- **Median+EMA**: Combines median filter (removes outliers/glitches) with EMA smoothing. Best for noisy environments with random color detection spikes.

- **Dynamic EMA**: Alpha scales based on movement speed. Snappier during fast movement, smoother during slow movement. `sensitivity` parameter controls responsiveness threshold.

## Configuration (GUI)
Launch the application to access the GUI.

### Home Tab
- Toggle Tracking: Start/Stop the tracker
- Master Enable: Must be enabled for hotkeys to work
- Smoothing: Controls mouse speed/humanization

### Aim Tab
- Aim At: Select body part (Head, Body, Legs)
- Filter Method: Prediction/smoothing method
- Offsets: Fine-tune the aim point

### Detection Tab
- Target Color: Pick the color to track
- Tolerance: Color match tolerance
- FOV: Detection box size (smaller is faster)

### System Tab
- Target FPS: Detection loop rate
- Prediction: Enable to lead moving targets

## Hotkeys
- PageUp: Start tracking
- PageDown: Stop tracking
- F12: Toggle debug console (if enabled)

## Troubleshooting
- Bot not moving:
  - Ensure Master Enable is enabled
  - Verify Target Color matches the target
  - Prefer Borderless Window mode if capture fails in fullscreen
- Performance issues:
  - Reduce FOV size
  - Lower Target FPS

## Development Checks
- Install test dependencies:
  ```bash
  python -m pip install pytest
  ```
- Run checks:
  ```bash
  ruff check .
  pyright .
  python -m pytest
  ```

## Disclaimer
This software is for educational and research purposes only. Use in online games may violate Terms of Service.
