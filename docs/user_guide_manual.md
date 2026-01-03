# Color Tracking Algo for Single Player Games in Development - V3.5.1 User Guide

## Introduction
The **Color Tracking Algo for Single Player Games in Development** (V3.5.1) is a hardened, professional-grade computer vision utility optimized for high-performance coordinate tracking and automated input research.

## Features
- **Stealth Mode**: Hide the GUI from OBS, Discord, and other capture tools using `SetWindowDisplayAffinity`.
- **Dynamic Hotkeys**: Rebind your start/stop keys instantly without restarting the app.
- **Hardened Core**: Thread-safe state management and leak-proof resource handling (GDI/Clipboard).
- **Extreme Speed Detection**: <2.5ms frame processing with cached FOV geometry and `mss` capture.
- **Predictive Stability**: Improved 1-Euro Filter with numerical stability fixes for high-FPS monitors.
- **Observability Probes**: High-resolution microsecond-level tracing for hot paths.
- **Titanium Class Optimizations**: Lock-based thread safety with transactional snapshot-reading.
- **Zero-Copy Buffer Management**: Direct `np.frombuffer` access to screen memory.
- **Smart Sleep**: Fused `time.sleep` and micro-spin-wait for nanosecond timing accuracy.


## Installation
1.  **Prerequisites**:
     *   Windows 10/11 (High-DPI aware)
     *   Python 3.12 or higher

2.  **Setup**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run**:
    ```bash
    python main.py
    ```

## Configuration (GUI)

### Header Section
- **Status**: Displays current tracking state (Idle, Scanning, Target Locked).
- **FPS**: Real-time loop frequency.
- **ACTIVATE TRACKING**: Main switch to Start/Stop the algo thread.

### COMBAT Tab
- **TARGET PRIORITY**:
    *   **Aim At**: Select target region (Head, Body, Legs).
- **Precision Offsets**:
    *   **Head Offset**: Vertical adjustment when aiming at HEAD.
    *   **Leg Offset**: Vertical adjustment when aiming at LEGS.
- **MOTION PHYSICS (1 Euro Filter)**:
    *   **Stabilization (Min Cutoff)**: Lower (0.1) = Heavy/Smooth. High (25.0) = Raw/Responsive.
    *   **Reflex Speed (Beta)**: Higher = Faster reaction to sudden direction changes.
    *   **Velocity Prediction**: Velocity lookahead multiplier. Set to **0.0** to disable prediction.
    *   **Adaptive Clamping**: Proximity-based damping prevents overshooting when approaching targets.
- **RESET**:
    *   **RESET MOTION SETTINGS**: Reverts only the Combat/Motion settings to defaults.

### VISION Tab
- **COLOR SPECTRUM**:
    *   **PICK SCREEN COLOR**: Enter Precision Lens magnifier mode. Use the circular viewport with crosshair to precisely select colors, with real-time HEX/RGB/XY telemetry in the dynamic data pill. Press ESC to cancel.
    *   **RGB Sliders**: Manual fine-tuning of target color.
    *   **Preview Box**: Shows current selected target color.
- **Tolerance (Match Width)**:
    *   **Slider**: How 'strict' the color match is. Lower = Stricter.
    *   **Tolerance Visualizer**: Shows the allowed color range based on tolerance.
- **FIELD OF VIEW (FOV)**:
    *   **W/H**: Detection area size. Smaller areas yield higher FPS.
    *   **Show Overlay (Green Box)**: Toggles the green FOV visualizer on screen.
- **RESET**:
    *   **RESET VISION SETTINGS**: Reverts only the Vision/Color settings to defaults.

### SYSTEM Tab
- **INPUT BINDINGS**: Displays current PageUp/PageDown hotkeys. Automatically checks for conflicts.
- **LOGS & BACKUP**:
    *   **OPEN LOGS FOLDER**: Opens the directory containing application logs for troubleshooting.
    *   **QUICK BACKUP**: Creates a timestamped copy of your configuration (`config.json.BAK`).
- **PRESETS**: Select from pre-tuned configurations (Default, Aggressive, Precise, High FPS). Selection is remembered across restarts.
- **STEALTH MODE**: Enable to hide the GUI from screen capture software (requires SYSTEM tab access).
- **PERFORMANCE**:
    *   **Target FPS Loop**: Max cycles per second for the core thread (30-1000).
- **DEBUGGING**:
    *   **Enable Debug Console**: Toggles the F12 clinical logs console.
- **RESET**:
    *   **RESET ALL SETTINGS**: Reverts `config.json` to factory defaults immediately.

### STATS Tab
- **Real-Time Analytics**: Current FPS, Avg Latency, 1% Lows, and Missed Frames.
- **History Graphs**: 1000-frame history for FPS and Latency/Detection times.

## 🧠 Advanced Physics Tuning (`config.json`)
The **1 Euro Filter** manages the tradeoff between jitter and lag:
- **`motion_min_cutoff`**: Minimum cutoff frequency. Low (0.01-0.1) for zero jitter at rest.
- **`motion_beta`**: Velocity relationship. High (0.05-0.3) to eliminate lag during fast tracking.

### Orchestration & Loop Timing
V3.4.1 uses a **Hybrid Precision Timing Loop**:
1. **Coarse Sleep**: For frame intervals >3ms, the system uses `time.sleep()`.
2. **Nanosecond Spin-Wait**: For the final micro-intervals, the system busy-waits for $\pm 0.05$ms precision.

## 👮 Verification Loop
Execute from project root:
1. **Linting**: `python -m ruff check .`
2. **Type Safety**: `python -m pyright .`
3. **Logic Integrity**: `python -m pytest`

## Hotkeys
- **PageUp**: Start Tracking
- **PageDown**: Stop Tracking
- **F12**: Toggle Debug Console (If enabled)

## Troubleshooting
- **No Movement?** Verify "ACTIVATE TRACKING" is pressed. Borderless Window mode is required.
- **Jitter?** Decrease `min_cutoff` or increase `Tolerance`.
- **Lag?** Increase `beta` or reduce the FOV size.

## Disclaimer
Educational and research use only. Adhere to all third-party Terms of Service.
