# Release Notes - SAI Color Tracker Algorithm V3.2.1 (Performance Release)

We are proud to announce the release of **V3.2.1**, a surgical performance and stability update focused on core engine efficiency and system transparency.

## 🚀 Performance Breakthroughs

### 🔧 OneEuroFilter Optimization (V3.2.1)
The detection loop's hot-path has been significantly tightened.
- **Attribute Access Speed**: Implemented `__slots__` in the `OneEuroFilter` class, reducing memory footprint and bypassing the expensive `__dict__` lookup for filter state variables.
- **Method Call Elimination**: All critical smoothing math (smoothing factor and exponential smoothing) has been **inlined** into the `__call__` method. This eliminates the overhead of small function calls thousands of times per second, reclaiming valuable CPU cycles for higher FPS.

### 🖼 Zero-Copy Screen Capture
Integrated a zero-copy buffer architecture using `np.frombuffer`. The system now creates a direct view into the raw BGRA memory captured by `mss`, eliminating the costly memory allocation and copy phase per frame.

## 🛡 Stability & Safety

### 🔒 Coordinate Clamping & Validation
- **Clamped Injection**: Precise screen-coordinate clamping (0-65535) is now enforced before the Windows `SendInput` call, preventing out-of-bounds cursor behavior.
- **FOV Enforcement**: Local search logic now strictly respects global FOV boundaries, preventing the "locked" target from dragging the detection system outside of specified limits.

### 🩹 Self-Healing Configuration
- **Type-Repair Logic**: The configuration system now automatically detects and repairs numerical "poisoning" (e.g., MagicMock instances or string corruption) to ensure the system never crashes due to invalid JSON state.

## 📄 Usability & Documentation

### 📝 Documented Config
The `config.json` file has been upgraded with a comprehensive inline guide. Every parameter is now explained in-file, including recommended values and tuning tips for competitive performance.

### 📊 Transparent Analytics
Real-time tracking of 1% frame lows and missed frame counts is now more accurate, allowing for clinical performance tuning of high-refresh-rate systems (up to 960 FPS).

---
*Note: This release is optimized for local development and research. Always use responsibly.*
