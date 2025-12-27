# SAI Color Tracking Algorithm V3 - User Guide

## Introduction
The SAI Color Tracking Algorithm V3 is a high-performance color detection and tracking tool designed for gaming assistance. It uses advanced computer vision to detect specific colors on screen and automatically moves the mouse cursor to the target.

## Features
- **Ultra-Fast Detection**: Optimized `mss` screen capture and parallel processing.
- **Unified Motion Engine**: Implements the **1 Euro Filter** for adaptive jitter reduction and lag minimization.
- **Velocity Prediction**: Predictive tracking to lead targets based on movement speed.
- **Visual Feedback**: Real-time FOV overlay and color tolerance preview.
- **Self-Healing Config**: Automatically repairs corrupted configuration files.

## Installation
1.  **Prerequisites**:
    *   Windows 10/11
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
Launch the application to access the GUI.

### Home Tab
- **Toggle Tracking**: Main switch to Start/Stop the bot.
- **Master Enable**: Safety switch. Must be CHECKED for hotkeys to work.
- **Hotkeys**: Displays current keybinds (Default: PageUp/PageDown).

### Aim Tab
- **Targeting Settings**:
    *   **Aim At**: Select Body Part (Head, Body, Legs).
- **Motion Engine (1 Euro Filter)**:
    *   **Stabilization (Min Cutoff)**: Controls smoothness. Lower values (0.001 - 0.1) reduce jitter but may feel "floaty".
    *   **Responsiveness (Beta)**: Controls how fast the cursor reacts to sudden changes. Higher values (0.001 - 0.1) reduce lag during fast movement.
    *   **Prediction Scale**: Velocity lookahead multiplier. Set to **0.0** to disable prediction.
- **Micro-Adjustments**:
    *   **Head Offset**: Pixels to aim *above* the detected center (for headshots).
    *   **Legs Offset**: Pixels to aim *below* the detected center.

### Detection Tab
- **Color Sensing**:
    *   **Target Color**: Click the color picker to select the enemy outline color.
    *   **Tolerance**: How strict the color match is. Use the visual preview button to check the range. Snaps to 5-unit increments.
- **Search Area (FOV)**:
    *   **Width/Height**: Size of the detection box in pixels. Smaller is faster. Snaps to 25px increments.
    *   **Show Visual Search Box**: Toggles a green rectangle overlay showing the detection area.

### System Tab
- **Performance**:
    *   **Target FPS**: Sets the detection loop speed. Recommended: 240+ for high performance, 120 for lower CPU usage. Snaps to 120fps increments.
- **Reset**:
    *   **Reset All Settings**: Reverts configuration to factory defaults.

## Stats & Debugging
### Stats Tab
- **Real-Time Analytics**:
    *   **FPS**: Current detection loop rate.
    *   **Latency**: Average processing time per frame (ms).
    *   **1% Lows**: The lowest FPS recorded (indicator of stutter).
    *   **Missed Frames**: Count of frames where processing took longer than the target interval.

### Debug Console (F12)
Enabled via `debug_mode: true` in `config.json`. Provides real-time logs for:
- Performance Stats
- Detection Events
- System State Changes
- Input/Movement Events

## Advanced Configuration (config.json)
Some settings are only accessible by editing the `config.json` file directly:
- **`screen_width` / `screen_height`**: **CRITICAL**. Must match your monitor resolution for accurate aiming. Defaults: 1920x1080.
- **`search_area`**: Radius (in pixels) for the optimized local search. If a target is found, the bot only scans this area around the target in the next frame. Default: 100.
- **`debug_mode`**: Set to `true` to enable the `F12` debug console hotkey. Default: `false`.
- **`ultra_responsive_mode`**: (Hidden) Set to `true` to prioritize input speed over stability. May cause jitter.
- **`zero_latency_mode`**: (Hidden) Set to `true` to bypass some smoothing filters for maximum responsiveness.

## Hotkeys
- **PageUp**: Start Tracking
- **PageDown**: Stop Tracking
- **F12**: Toggle Debug Console (Requires `debug_mode: true` in `config.json`)

## Troubleshooting
- **Bot not moving?**
    *   Check "Master Enable" is Checked.
    *   Verify "Target Color" matches the enemy.
    *   Ensure game is in "Borderless Window" mode (Fullscreen optimization may block screen capture).
- **Jittery movement?**
    *   Lower **Stabilization (Min Cutoff)** in the Aim tab.
    *   Increase **Tolerance** in Detection tab if the color is flickering.
- **Laggy tracking?**
    *   Increase **Responsiveness (Beta)** in the Aim tab.
    *   Reduce **FOV** size.
    *   Check **Stats tab** for FPS drops.

## Disclaimer
This software is for educational and research purposes only. Use in online games may violate Terms of Service.