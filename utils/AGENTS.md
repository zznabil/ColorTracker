# UTILS: INFRASTRUCTURE & SERVICE LAYERS

## OVERVIEW

The `utils/` layer provides a deterministic foundation for the application. It handles O(1) configuration management, microsecond-accurate telemetry, and rate-limited logging. These services are designed to be "invisible" to the hot-path—minimizing overhead through lockless patterns, atomic operations, and debounced persistence.

## WHERE TO LOOK

| Service | File | Role |
|---------|------|------|
| **Config** | `utils/config.py` | Versioned state management with self-healing JSON persistence and Observer pattern. |
| **Telemetry** | `utils/performance_monitor.py` | Ring-buffer based metric tracking and high-res timing probes (`start_probe`/`stop_probe`). |
| **Logger** | `utils/logger.py` | Rate-limited logging with spam prevention and DearPyGui debug console integration. |
| **Input** | `utils/keyboard_listener.py` | Asynchronous hotkey management and rebind logic via `pynput`. |
| **Paths** | `utils/paths.py` | Robust path resolution for both standard execution and frozen PyInstaller states. |
| **Display** | `utils/screen_info.py` | DPI-aware geometry and screen resolution discovery. |

## SINGULARITY UPDATES (V3.4.2)

- **Telemetry Singularity**: Refactored `PerformanceMonitor.stop_probe` to use `dict.pop()`, eliminating redundant containment checks and attribute lookup depth.
- **Loop Hoisting**: Version synchronization and health monitoring logic moved to a 500-frame throttle in the main loop service.

## CONVENTIONS

- **Atomic Config Persistence**: All saves use a `write -> rename` pattern to prevent file corruption.
- **Lockless Telemetry**: `PerformanceMonitor` uses a single-writer pattern for the logic loop; readers use `get_probe_stats()` which perform atomic snapshot copies.
- **O(1) Version Check**: The logic loop MUST check `config._version` before executing expensive recalculations or state transitions.
- **High-Res Timing**: Always use `time.perf_counter_ns()` for telemetry to ensure microsecond precision.
- **Debounced Saves**: Config changes are debounced (default 500ms) to prevent I/O saturation.

## ANTI-PATTERNS

- **Blocking I/O in Hot-Path**: Never perform disk writes or blocking network calls in telemetry probes or the main logic loop.
- **Global `print()` Statements**: Use `logger.info()` or `logger.debug()` to ensure rate-limiting and visibility in the DPG console.
- **Raw Path Strings**: Always use `utils.paths.get_app_dir()` to avoid issues in packaged/portable environments.
- **Manual Lock Contention**: Avoid taking locks in `PerformanceMonitor` for simple increments; favor the single-writer pattern.
