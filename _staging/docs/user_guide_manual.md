# SAI Color Tracking Algorithm V3 - User Guide

## Introduction
The SAI Color Tracking Algorithm V3 is a high-performance color detection and tracking tool designed for gaming assistance. It uses advanced computer vision to detect specific colors on screen and automatically moves the mouse cursor to the target.

## Features
- **Ultra-Fast Detection**: Optimized `mss` screen capture and parallel processing.
- **Predictive Tracking**: Kalman-filter-like algorithms (1 Euro Filter, EMA, etc.) to predict target movement.
- **Human-Like Smoothing**: Adjustable smoothing to mimic natural mouse movement.
- **Overlay HUD**: Visual FOV overlay to see exactly where the bot is looking.
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
- **Smoothing**: Controls mouse speed/humanization.
    *   *Low (0-0.5)*: Pro/Fast.
    *   *High (2.0+)*: Smooth/Legit.

### Aim Tab
- **Aim At**: Select Body Part (Head, Body, Legs).
- **Filter Method**: Algorithm for movement prediction (EMA is standard).
- **Offsets**: Fine-tune the aim point (e.g., aim slightly higher for headshots).

### Detection Tab
- **Target Color**: Click the color picker to select the enemy outline color (Purple/Red recommended).
- **Tolerance**: How strict the color match is. Increase if lighting varies.
- **FOV (Field of View)**: size of the detection box. Smaller = Faster.

### System Tab
- **Target FPS**: Detection loop speed. 240+ recommended.
- **Prediction**: Enable to lead shots on moving targets.

## Hotkeys
- **PageUp**: Start Tracking
- **PageDown**: Stop Tracking
- **F12**: Toggle Debug Console (if enabled)

## Troubleshooting
- **Bot not moving?**
    *   Check "Master Enable" is Checked.
    *   Verify "Target Color" matches the enemy.
    *   Ensure game is in "Borderless Window" mode (Fullscreen optimization may block screen capture).
- **Laggy?**
    *   Reduce FOV size.
    *   Lower Target FPS to 120.

## Disclaimer
This software is for educational and research purposes only. Use in online games may violate Terms of Service.
