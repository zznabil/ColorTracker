# Performance Analysis & FPS Limits

## 📉 Bottleneck Investigation
We investigated the reported "stuck at ~120 FPS" issue. While the software VSync cap has been removed, a **physical bottleneck** exists in the screen capture technology.

### 1. MSS Capture Limit (CPU Bound)
The current capture library (`mss`) relies on the GDI/BitBlt API, which performs a CPU-based memory copy of the screen.

**Benchmark Results (`tools/benchmark_mss.py`):**
- **1080p Full Screen**: ~40 FPS (25ms latency)
- **500x500 Region**: ~120 FPS (8.3ms latency)
- **200x200 Region** (Tracking Mode): **~170-180 FPS** (5.5ms latency)

### 2. The "Real-World" FPS Ceiling
While the tracking logic runs in microseconds, the **Screen Capture** step takes ~5.5ms per frame.
- **Theoretical Max**: 1000ms / 5.5ms ≈ **181 FPS**
- **Practical Max** (with logic + input overhead): **~160-170 FPS**

### 3. Why ~120 FPS?
If you are seeing ~120 FPS specifically:
1.  **DWM Composition**: Windows Desktop Window Manager (DWM) often syncs updates to the monitor refresh rate. Even if we capture faster, we might be capturing duplicate frames or hitting a driver timing wall.
2.  **Overhead**: The remaining 2-3ms overhead (Input + Logic + OS Scheduling) brings the 180 FPS theoretical max down closer to 120-140 FPS.

## 🛠️ Solutions Implemented
1.  **Unlocked VSync**: Removed the hard 60/144Hz cap in the GUI.
2.  **Timer Resolution**: Enforced 1ms Windows Timer Resolution to prevent sleep drift.
3.  **Thread Priority**: Capped GUI thread to 60 FPS to give Logic thread 100% CPU focus.

## 🚀 Future Optimization Path
To break the 180 FPS barrier and reach 240/360 FPS, the tracking engine must migrate from **MSS (CPU)** to **DXGI (GPU)** capture.

**Recommended Upgrade:**
- **Library**: `dxcam` or `bettercam`
- **Technology**: DirectX Desktop Duplication API
- **Expected Performance**: 300+ FPS with <1ms capture latency.

**Current Status**: The application is running at the maximum speed physically possible with the current `mss` architecture.