# THE ARTISAN: GUI & HUD SUBSYSTEM

**Directory:** `gui/`  
**Archetype:** Artisan (Visual Excellence & Interaction)

## OVERVIEW

The Artisan manages a GPU-accelerated HUD and non-interactive viewport overlays. It provides a high-performance visual layer using **DearPyGui** that operates independently of core logic threads. Its primary mission is to provide real-time performance auditing and intuitive feedback without introducing latency or input capture.

## WHERE TO LOOK

| Component | File | Role |
|-----------|------|------|
| **Core GUI Setup** | `main_window.py` | Initializes DPG, manages the lifecycle of tabs and viewports. |
| **Viewport HUD** | `main_window.py` | High-performance FOV and target overlays via `add_viewport_drawlist`. |
| **Analytics Engine** | `main_window.py` | Real-time plotting of 1% low FPS and detection latency. Now supports high-resolution **Singularity Telemetry**. |
| **Theme Engine** | `main_window.py` | GPU-driven styling and color tolerance visualizers for "Vision" setup. |
| **Thread Safety Interface** | `main.py` | `move_to_target()` delegation method providing safe cross-thread access to movement system. |

## SINGULARITY UPDATES (V3.4.2)

- **High-Res Analytics**: UI now consumes atomic snapshots from the Singularity-grade performance monitor.
- **Loop Throttling Visibility**: Performance HUD reflects the impact of 500-frame hoisting optimizations on jitter reduction.

## CONVENTIONS

- **Non-Blocking Viewports**: Always use `dpg.add_viewport_drawlist(front=True)` for overlays (FOV, crosshairs) to ensure zero input interference with the game.
- **Rate-Limited Snapshots**: UI elements (analytics, status bars) must pull from `PerformanceMonitor` snapshots rather than direct core memory to avoid cache thrashing.
- **Immediate Visual Feedback**: Configuration changes (FOV size, color targets) must render visual previews instantly to assist user calibration.
- **DPI Scaling**: All geometry calculations must respect system DPI settings to maintain overlay accuracy on 4K/High-DPI displays.

## ANTI-PATTERNS

- **Blocking Logic**: Never perform I/O, vision processing, or complex math in DPG callbacks; offload to Sage (`core/`).
- **Input Capture**: Do not use standard `dpg.window` for game-time overlays, as they capture mouse clicks and keyboard focus.
- **Logic Leakage**: GUI code should never calculate tracking offsets or motion delta; it only *displays* results from `PerformanceMonitor`.
- **Direct Variable Polling**: Avoid polling `self.config` directly in high-frequency draw loops; use the observer pattern or version-checked local caches.
