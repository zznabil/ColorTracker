# Color Tracking Algo for Single Player Games in Development - V3.5.0 User Guide

## Introduction
The **Color Tracking Algo for Single Player Games in Development** (V3.5.0) is a professional-grade computer vision utility optimized for high-performance coordinate tracking and automated input research.

## Features
- **Extreme Speed Detection**: GPU-accelerated frame processing with cached FOV geometry and `mss` capture.
- **Predictive Stability Logic**: Deceleration dampening and direction-flip suppression to prevent high-scale overshooting.
- **Chebyshev Velocity Gating**: Max(dx, dy) speed estimation to resolve vertical prediction deadzones.
- **Observability Probes**: High-resolution microsecond-level tracing for hot paths (`start_probe`/`stop_probe`).
- **Titanium Class Optimizations**: Lockless telemetry snapshots $O(0 \text{ contention})$ and version-based config propagation.
- **Orchestration Gems**: Loop-level method caching and config hot-reload throttling for peak throughput (30-1000 FPS).
- **Zero-Copy Buffer Management**: Direct `np.frombuffer` access to screen memory avoids O(N) allocation overhead.
- **Allocation-Free Interaction**: Reuses `ctypes` input structures and caches function pointers to prevent memory allocation churn.
- **Smart Sleep (Hybrid Precision Sync)**: Fused `time.sleep` and micro-spin-wait for nanosecond timing accuracy via `_smart_sleep`.
- **Adaptive Predictive Tracking**: Real-time velocity-based projection to eliminate smoothing-induced lag.

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

### SYSTEM Tab
- **INPUT BINDINGS**: Displays current PageUp/PageDown hotkeys.
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
