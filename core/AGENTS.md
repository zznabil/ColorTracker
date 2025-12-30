# CORE KNOWLEDGE BASE (THE SAGE)

## OVERVIEW

The performance-critical engine: Vision hot-paths, adaptive motion smoothing, and zero-allocation WinAPI input.

## WHERE TO LOOK
- **Detection Engine**: `core/detection.py` - MSS (thread-local), `np.frombuffer` views, `cv2.minMaxLoc` search. Achieves **Branchless Hot-Path** via eager cache warming.
- **Motion Engine**: `core/motion_engine.py` - 1 Euro Filter, `__slots__` state, Chebyshev velocity gating.
- **Input Injection**: `core/low_level_movement.py` - `SendInput` pre-allocation, function pointer caching, thread-safe delegation interface. Now includes **Eager Hardware Metrics** initialization.

## SINGULARITY OPTIMIZATIONS (V3.4.2)

- **Branchless Execution**: Zero `if` checks for uninitialized caches in frame processing.
- **Eager Initialization**: Constructors now pre-warm all FOV, bounds, and screen scaling metrics.
- **Lockless Telemetry**: Integrated with `PerformanceMonitor`'s atomic `pop()` functionality.

## CONVENTIONS

- **O(1) Memory**: Zero object allocation in hot paths (`find_target`, `process`, `move_mouse`).
- **Hoisting**: Localize `self` attributes to function scope before loops to skip lookup overhead.
- **Pre-allocation**: Reuse `_capture_area` dicts and C-structs (`INPUT`, `MOUSEINPUT`, `POINT`).
- **Math Optimization**: 
  - Hoist division to multiplication: `x * scale` instead of `x / width`.
  - Fast rounding: `int(val + 0.5)` for positive coordinate conversion.
  - Inline smoothing arithmetic: No helper calls in `OneEuroFilter.__call__`.
- **Concurrency**: `mss.mss()` must be `threading.local()` to prevent `ScreenShotError`.
- **Attribute Access**: Never `while: self.config.x`. Hoist to local `x` once.

## ANTI-PATTERNS

- **Allocations**: No `dict`, `list`, or `tuple` creation in frame processing loops.
- **Numpy Scalars**: Avoid converting single values to numpy types (massive overhead).
- **Relative Aiming**: Forbidden. Use absolute (0-65535) coordinates for consistency and stealth.
- **Redundant Syscalls**: Reuse `dt`/`time` deltas; avoid calling `perf_counter` inside filters.
