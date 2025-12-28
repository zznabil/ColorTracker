# Color Tracking Algo for Single Player Games in Development - V3.3.0 User Guide

## Introduction
The **Color Tracking Algo for Single Player Games in Development** (V3.3.0) is a professional-grade computer vision utility optimized for high-performance coordinate tracking and automated input research.

## Features
- **Extreme Speed Detection**: GPU-accelerated frame processing with cached FOV geometry and `mss` capture.
- **Titanium Class Optimizations**: Lockless telemetry snapshots $O(0 \text{ contention})$ and version-based config propagation.
- **Orchestration Gems**: Loop-level method caching and config hot-reload throttling for peak 960 FPS throughput.
- **Zero-Copy Buffer Management**: Direct `np.frombuffer` access to screen memory avoids O(N) allocation overhead.
- **Allocation-Free Interaction**: Reuses `ctypes` input structures to prevent memory allocation churn.
- **Hybrid Precision Sync**: Fused `time.sleep` and micro-spin-wait for nanosecond timing accuracy.
- **Adaptive Predictive Tracking**: Real-time velocity-based projection to eliminate smoothing-induced lag.

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
- **Micro-Adjustments (Spatial Correction)**:
    *   **Head Offset**: Distance (pixels) to aim **ABOVE** the detected center. Internally processed as a negative subtraction.
    *   **Legs Offset**: Distance (pixels) to aim **BELOW** the detected center. Internally processed as a positive addition.

### Detection Tab
- **Color Sensing**:
    *   **Target Color**: Click the color picker to select the specific outline or center color.
    *   **Tolerance**: How strict the match is (0-255). Snaps to 5-unit increments. Uses a 2.5x gain factor for detection stability.
- **Search Area (FOV)**:
    *   **Width/Height**: Detection area size. Smaller areas yield higher FPS. Snaps to 5px increments. Lower limit 5px.
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

## 🧠 Advanced Physics Tuning (`config.json`)
The **1 Euro Filter** manages the tradeoff between jitter and lag using two main parameters:
- **`motion_min_cutoff` ($f_{c_{min}}$)**: The minimum cutoff frequency. A lower value (0.01-0.1) creates a "heavy" feel with zero jitter at rest.
- **`motion_beta` ($\beta$)**: The velocity relationship. A higher value (0.05-0.5) allows the cutoff frequency to increase rapidly with speed, eliminating lag during fast tracking.
- **`ultra_responsive_mode`**: Prioritizes raw throughput for high-refresh monitors.
- **`zero_latency_mode`**: Surgical bypass of non-essential smoothing buffers.

### Orchestration & Loop Timing
V3.2.3 introduces a **Hybrid Precision Timing Loop**:
1. **Coarse Sleep**: For frame intervals >1ms, the system uses `time.sleep(90%)` to yield CPU cycles.
2. **Nanosecond Spin-Wait**: For the final micro-intervals, the system enters a tight `while` loop to ensure frame release within $\pm 0.05$ms precision.
3. **Internal Caching**: All high-frequency attribute lookups (e.g., `self.detection.find_target`) are pre-cached as local variables before entering the loop.

## 👮 The Policeman (Verification Loop)
To ensure the algo is running at peak performance and adheres to the architectural standards, execute the following from the project root:
1. **Linting**: `python -m ruff check .`
2. **Type Safety**: `python -m pyright .`
3. **Logic Integrity**: `python -m pytest`

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