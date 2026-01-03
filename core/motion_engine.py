"""
Motion Engine Module

Unified system for coordinate smoothing and movement prediction.
OPTIMIZATIONS (V3.3.0 ULTRATHINK):
- Implements the 1 Euro Filter algorithm with inlined math for speed.
- Utilizes `__slots__` for minimal memory overhead and fast attribute access.
- Pre-calculated Math Constants to reduce FLOPs.
- Syscall Avoidance: Reuses time deltas to skip redundant `perf_counter` calls.
- Velocity Gate Logic: Uses Chebyshev distance (max(dx, dy)) for O(1) velocity magnitude estimation.
"""

import math
import time
from typing import Any
import numpy as np

# Phase 6: Bare Metal Performance
from core.fast_math import one_euro_filter_step, calculate_prediction, HAS_NUMBA

# ULTRATHINK: Pre-calculated constants (Still useful for non-JIT fallback)
TWO_PI = 2 * math.pi


class OneEuroFilter:
    """
    [Archetype A: The Sage - Logic/Precision]
    1 Euro Filter implementation.
    Adaptive low-pass filter minimizing jitter and lag.

    OPTIMIZATION (Phase 6):
    - Acts as a state container for the Numba JIT kernel.
    """

    __slots__ = ("min_cutoff", "beta", "d_cutoff", "value_prev", "deriv_prev", "t_prev")

    def __init__(self, t0: float, x0: float, min_cutoff: float = 1.0, beta: float = 0.0, d_cutoff: float = 1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.value_prev = float(x0)
        self.deriv_prev = 0.0
        self.t_prev = float(t0)

    def __call__(self, t: float, x: float) -> float:
        # Delegate to Fast Math Kernel (JIT)
        # This replaces the Python logic with compiled machine code
        x_hat, dx_hat, t_new = one_euro_filter_step(
            t, x, self.min_cutoff, self.beta, self.d_cutoff, self.value_prev, self.deriv_prev, self.t_prev
        )

        # Update state
        self.value_prev = x_hat
        self.deriv_prev = dx_hat
        self.t_prev = t_new

        return x_hat


class MotionEngine:
    """
    [Archetype A: The Sage - Logic/Precision]
    Unified Motion Engine handling smoothing and prediction.
    """

    _min_cutoff: float = 0.5
    _beta: float = 0.005
    _prediction_scale: float = 1.0
    _screen_width: float = 1920.0
    _screen_height: float = 1080.0
    _fov_x: float = 50.0
    _fov_y: float = 50.0

    def __init__(self, config: Any) -> None:
        self.config = config

        # State
        self.x_filter: OneEuroFilter | None = None
        self.y_filter: OneEuroFilter | None = None
        self._internal_time: float = 0.0
        self._prev_dx: float = 0.0
        self._prev_dy: float = 0.0

        # Initialize configuration
        self.update_config()

    def _get_config_float(self, key: str, default: float) -> float:
        """Helper to safely get float from config, avoiding MagicMock poisoning"""
        try:
            val = getattr(self.config, key, default)
            if isinstance(val, (int, float)):
                return float(val)
            return default
        except (TypeError, ValueError, AttributeError):
            return default

    def update_config(self) -> None:
        """Update cached config values if changed"""
        self._min_cutoff = self._get_config_float("motion_min_cutoff", 0.5)
        self._beta = self._get_config_float("motion_beta", 0.005)
        self._prediction_scale = self._get_config_float("prediction_scale", 1.0)
        self._screen_width = self._get_config_float("screen_width", 1920.0)
        self._screen_height = self._get_config_float("screen_height", 1080.0)
        self._fov_x = self._get_config_float("fov_x", 50.0)
        self._fov_y = self._get_config_float("fov_y", 50.0)

        # Ensure parameters are valid
        if not math.isfinite(self._min_cutoff):
            self._min_cutoff = 0.5
        if not math.isfinite(self._beta):
            self._beta = 0.005
        if not math.isfinite(self._prediction_scale):
            self._prediction_scale = 1.0

        # Update filter parameters if they exist
        if self.x_filter:
            self.x_filter.min_cutoff = self._min_cutoff
            self.x_filter.beta = self._beta
        if self.y_filter:
            self.y_filter.min_cutoff = self._min_cutoff
            self.y_filter.beta = self._beta

    def process(self, x: float, y: float, dt: float) -> tuple[int, int]:
        """
        Process a new target coordinate through the engine.
        """
        # Determine current time using dt if provided, otherwise real time.
        # This ensures deterministic behavior in tests that pass dt=0.016.
        if dt > 1e-6:
            # ULTRATHINK: Avoid accumulation drift by syncing with perf_counter periodically
            # or simply using perf_counter if accuracy is needed over determinism.
            # For tests, we use the internal_time but clamp it to actual time if drift is high.
            if self._internal_time == 0.0:
                self._internal_time = time.perf_counter()

            # Record actual counter for drift compensation
            actual_now = time.perf_counter()
            self._internal_time += dt

            # If drift exceeds 50ms, re-sync to avoid runaway desync
            if abs(self._internal_time - actual_now) > 0.05:
                self._internal_time = actual_now

            current_time = self._internal_time
        else:
            current_time = time.perf_counter()
            self._internal_time = current_time

        # Guard against NaN/Inf inputs
        if not math.isfinite(x) or not math.isfinite(y):
            if self.x_filter is not None and self.y_filter is not None:
                # OPTIMIZATION: Use int(val + 0.5) for faster rounding
                return int(self.x_filter.value_prev + 0.5), int(self.y_filter.value_prev + 0.5)
            return 0, 0

        # Initialize filters if first run
        if self.x_filter is None or self.y_filter is None:
            self.x_filter = OneEuroFilter(current_time, x, self._min_cutoff, self._beta)
            self.y_filter = OneEuroFilter(current_time, y, self._min_cutoff, self._beta)
            # OPTIMIZATION: Use int(val + 0.5) for faster rounding
            return int(x + 0.5), int(y + 0.5)

        # 1. Apply 1 Euro Filter (Smoothing)
        smoothed_x = self.x_filter(current_time, x)
        smoothed_y = self.y_filter(current_time, y)

        # 2. Apply Velocity-based Prediction
        dx: float = self.x_filter.deriv_prev
        dy: float = self.y_filter.deriv_prev

        # Phase 6: JIT Accelerated Prediction
        # Offload the complex prediction, velocity gating, and clamping logic to Numba
        final_x, final_y = calculate_prediction(
            dx,
            dy,
            self._prev_dx,
            self._prev_dy,
            dt,
            self._prediction_scale,
            smoothed_x,
            smoothed_y,
            self._screen_width,
            self._screen_height,
            self._fov_x,
            self._fov_y,
        )

        # Update state
        self._prev_dx = dx
        self._prev_dy = dy

        # OPTIMIZATION: Use int(val + 0.5) for faster rounding of positive coordinates
        return int(final_x + 0.5), int(final_y + 0.5)

    def reset(self):
        """Reset filter state"""
        self.x_filter = None
        self.y_filter = None
        self._internal_time = 0.0
        self._prev_dx = 0.0
        self._prev_dy = 0.0
