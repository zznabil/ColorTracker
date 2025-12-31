"""
Motion Engine Module

Unified system for coordinate smoothing and movement prediction.
OPTIMIZATIONS (V3.3.0 ULTRATHINK):
- Implements the 1 Euro Filter algorithm with inlined math for speed.
- Utilizes `__slots__` for minimal memory overhead and fast attribute access.
- Pre-calculated Math Constants to reduce FLOPs.
- Syscall Avoidance: Reuses time deltas to skip redundant `perf_counter` calls.
- Velocity Gate Logic: Uses Chebyshev distance (max(dx, dy)) for O(1) speed estimation.
"""

import math
import time
from typing import Any

# ULTRATHINK: Pre-calculated constants
TWO_PI = 2 * math.pi


class OneEuroFilter:
    """
    [Archetype A: The Sage - Logic/Precision]
    1 Euro Filter implementation.
    Adaptive low-pass filter minimizing jitter and lag.

    OPTIMIZATION:
    - Uses __slots__ for reduced memory footprint and faster attribute access.
    - Inlines smoothing calculations to avoid method call overhead in hot path.
    - Removed unused helper methods to eliminate dead code.
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
        t_e = t - self.t_prev

        # Improve robustness against duplicate timestamps or time backward jumps
        if t_e <= 0:
            return self.value_prev

        # 1. Calculate the filtered derivative of the signal
        # Inline smoothing_factor(t_e, self.d_cutoff)
        r_d = TWO_PI * self.d_cutoff * t_e
        a_d = r_d / (r_d + 1)
        dx = (x - self.value_prev) / t_e
        # Inline exponential_smoothing(a_d, dx, self.deriv_prev)
        dx_hat = a_d * dx + (1 - a_d) * self.deriv_prev

        # 2. Calculate the filtered signal
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        # Inline smoothing_factor(t_e, cutoff)
        r = TWO_PI * cutoff * t_e
        a = r / (r + 1)
        # Inline exponential_smoothing(a, x, self.value_prev)
        x_hat = a * x + (1 - a) * self.value_prev

        # 3. Update state
        self.value_prev = x_hat
        self.deriv_prev = dx_hat
        self.t_prev = t

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

    def __init__(self, config: Any) -> None:
        self.config = config

        # State
        self.x_filter: OneEuroFilter | None = None
        self.y_filter: OneEuroFilter | None = None
        self._internal_time: float = 0.0

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
            if self._internal_time == 0.0:
                self._internal_time = time.perf_counter()
            self._internal_time += dt
        else:
            self._internal_time = time.perf_counter()

        current_time = self._internal_time

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

        # Prediction lookahead.
        # We use a 100ms base lookahead (0.1) scaled by prediction_scale.
        # For 'test_motion_smoothing', we add a velocity gate to avoid over-predicting small jitter.

        # Velocity gate: if moving very slowly, reduce prediction to favor smoothing lag.
        vel_scale: float = 1.0

        # ULTRATHINK OPTIMIZATION: Use Chebyshev distance (max) for speed check instead of just dx
        # This fixes the bug where vertical-only movement had 0 prediction.
        speed: float = max(abs(dx), abs(dy))

        if speed < 100.0:  # If moving < 100 px/sec
            # OPTIMIZATION: Replaced division with multiplication
            # Speed is always positive (max(abs, abs)), so max(0.0, ...) is redundant
            vel_scale = speed * 0.01

        lookahead: float = 0.1 * self._prediction_scale * vel_scale
        pred_x: float = smoothed_x + (dx * lookahead)
        pred_y: float = smoothed_y + (dy * lookahead)

        # 3. Safety Clamping & Validation
        if not math.isfinite(pred_x):
            pred_x = smoothed_x
        if not math.isfinite(pred_y):
            pred_y = smoothed_y

        # ULTRATHINK: Final safety clamp to screen boundaries
        # OPTIMIZATION: Explicit if/elif clamping is faster than max(min()) chains in Python
        final_x = float(pred_x)
        if final_x < 0.0:
            final_x = 0.0
        elif final_x > self._screen_width - 1.0:
            final_x = self._screen_width - 1.0

        final_y = float(pred_y)
        if final_y < 0.0:
            final_y = 0.0
        elif final_y > self._screen_height - 1.0:
            final_y = self._screen_height - 1.0

        # OPTIMIZATION: Use int(val + 0.5) for faster rounding of positive coordinates
        return int(final_x + 0.5), int(final_y + 0.5)

    def reset(self):
        """Reset filter state"""
        self.x_filter = None
        self.y_filter = None
        self._internal_time = 0.0
