# Color Tracking Algo for Single Player Games in Development - User Guide

## Introduction
The **Color Tracking Algo for Single Player Games in Development** (V3.2) is a high-performance computer vision tool designed for research and educational purposes. It detects specific colors on-screen and automates mouse movement using low-level Windows APIs.

## Features
- **Ultra-Fast Detection**: Optimized `mss` screen capture using zero-copy `np.frombuffer` buffers.
- **Unified Motion Engine**: Implements the **1 Euro Filter** for adaptive jitter reduction and minimal lag.
- **Velocity Prediction**: Predictive lookahead to lead moving targets based on real-time velocity.
- **Visual Feedback**: Real-time FOV overlay and color tolerance preview via DearPyGui.
- **Self-Healing Config**: Automatically repairs or resets corrupted configuration files.
- **Direct Input**: Uses Windows `SendInput` for stealthy, hardware-like signal injection.

## Installation
1.  **Prerequisites**:
    *   Windows 10/11 (High-DPI aware)
    *   Python 3.11 or higher
2.  **Setup**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run**:
    ```bash
    python main.py
    ```

## Configuration (GUI)

### Home Tab
- **Toggle Tracking**: Main switch to Start/Stop the algo thread.
- **Master Enable**: Safety switch. Must be **CHECKED** for hotkeys and tracking to function.
- **Hotkeys**: Displays current keybinds (Default: PageUp to Start, PageDown to Stop).

### Aim Tab
- **Targeting Settings**:
    *   **Aim At**: Select target region (Head, Body, Legs).
- **Motion Engine (1 Euro Filter)**:
    *   **min_cutoff**: Controls smoothness. Lower values (e.g., 0.01) reduce jitter but increase lag.
    *   **beta**: Controls responsiveness. Higher values (e.g., 0.05) reduce lag during fast movement.
    *   **Prediction Scale**: Velocity lookahead multiplier. Set to **0.0** to disable prediction.
- **Micro-Adjustments (Logical Offsets)**:
    *   **Head Offset**: Pixels to aim **ABOVE** the detected center (Negative value in internal logic).
    *   **Legs Offset**: Pixels to aim **BELOW** the detected center (Positive value in internal logic).

### Detection Tab
- **Color Sensing**:
    *   **Target Color**: Click the color picker to select the specific outline or center color.
    *   **Tolerance**: How strict the match is (0-255). Snaps to 5-unit increments. Uses a 2.5x gain factor for detection stability.
- **Search Area (FOV)**:
    *   **Width/Height**: Detection area size. Smaller areas yield higher FPS. Snaps to 25px increments.
    *   **Show Visual Search Box**: Toggles the green FOV overlay.

### System Tab
- **Performance**:
    *   **Target FPS**: Loop speed (120-960 FPS). Snaps to 120fps increments. Higher FPS requires more CPU/GPU.
- **Reset**:
    *   **Reset All Settings**: Reverts `config.json` to factory defaults immediately.

## Stats & Analytics
### Stats Tab
- **Real-Time Analytics**:
    *   **FPS/Latency**: Shows current loop speed and processing delay (ms).
    *   **1% Lows**: Detects micro-stutters and frame-drops.
    *   **Missed Frames**: Count of frames failing to meet the target time interval.

### Debug Console (F12)
Accessible if `debug_mode` is enabled. Provides clinical logs for detection events, movement injection, and system errors.

## Advanced Tuning (`config.json`)
- **`search_area`**: Radius for optimized local search. If a target is locked, the algo only scans this radius around the last known position.
- **`ultra_responsive_mode`**: Prioritizes input frequency over signal stability.
- **`zero_latency_mode`**: Bypasses certain smoothing buffers for raw signal throughput.

## Hotkeys
- **PageUp**: Start Tracking
- **PageDown**: Stop Tracking
- **F12**: Toggle Debug Console (If enabled)

## Troubleshooting
- **No Movement?** Verify "Master Enable" is checked and "Target Color" is accurately picked. Borderless Window mode is required for most games.
- **Jitter?** Decrease `min_cutoff` or increase `Tolerance`.
- **Lag?** Increase `beta` or reduce the FOV size.

## Disclaimer
This software is for educational, research, and development purposes only. Use in commercial or online environments may violate third-party Terms of Service.