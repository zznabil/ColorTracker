"""
Motion Engine Module

Unified system for coordinate smoothing and movement prediction.
Implements the 1 Euro Filter algorithm for adaptive filtering:
- Low jitter at low speeds (high smoothing)
- Low latency at high speeds (low smoothing)
"""

import math
import time
from typing import Any


class OneEuroFilter:
    """
    1 Euro Filter implementation.
    Adaptive low-pass filter minimizing jitter and lag.
    """

    __slots__ = ("min_cutoff", "beta", "d_cutoff", "x_prev", "dx_prev", "t_prev")

    def __init__(self, t0: float, x0: float, min_cutoff: float = 1.0, beta: float = 0.0, d_cutoff: float = 1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_prev = float(x0)
        self.dx_prev = 0.0
        self.t_prev = float(t0)

    def smoothing_factor(self, t_e: float, cutoff: float) -> float:
        r = 2 * math.pi * cutoff * t_e
        return r / (r + 1)

    def exponential_smoothing(self, a: float, x: float, x_prev: float) -> float:
        return a * x + (1 - a) * x_prev

    def __call__(self, t: float, x: float) -> float:
        t_e = t - self.t_prev

        # Improve robustness against duplicate timestamps or time backward jumps
        if t_e <= 0:
            return self.x_prev

        # Calculate the filtered derivative of the signal
        a_d = self.smoothing_factor(t_e, self.d_cutoff)
        dx = (x - self.x_prev) / t_e
        dx_hat = self.exponential_smoothing(a_d, dx, self.dx_prev)

        # Calculate the filtered signal
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self.smoothing_factor(t_e, cutoff)
        x_hat = self.exponential_smoothing(a, x, self.x_prev)

        # Update state
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t

        return x_hat


class MotionEngine:
    """
    Unified Motion Engine handling smoothing and prediction.
    """

    _config_cache_version: int = -1
    _min_cutoff: float = 0.1
    _beta: float = 0.1
    _prediction_scale: float = 1.0

    def __init__(self, config: Any) -> None:
        self.config = config

        # State
        self.x_filter: OneEuroFilter | None = None
        self.y_filter: OneEuroFilter | None = None

        # Initialize configuration
        self.update_config()

    def update_config(self) -> None:
        """Update cached config values if changed"""
        # Assuming config has a version counter or just checking values directly
        # For this implementation, we'll pull fresh values to be safe
        # In a high-perf loop, we might want to check a dirty flag

        # Default safe values
        min_cutoff = getattr(self.config, "motion_min_cutoff", 0.05)
        beta = getattr(self.config, "motion_beta", 0.05)
        prediction_scale = getattr(self.config, "prediction_scale", 1.0)

        # Check validity
        if not math.isfinite(min_cutoff):
            min_cutoff = 0.05
        if not math.isfinite(beta):
            beta = 0.05
        if not math.isfinite(prediction_scale):
            prediction_scale = 1.0

        # Update cache
        self._min_cutoff = float(min_cutoff)
        self._beta = float(beta)
        self._prediction_scale = float(prediction_scale)

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

        Args:
            x: Raw target X coordinate
            y: Raw target Y coordinate
            dt: Time delta since last frame (not used primarily by 1euro, it uses timestamps)
                But we accept it for API compatibility if needed.

        Returns:
            Tuple[int, int]: Processed (smoothed & predicted) coordinates
        """
        current_time = time.perf_counter()

        # Guard against NaN/Inf inputs
        if not math.isfinite(x) or not math.isfinite(y):
            if self.x_filter is not None and self.y_filter is not None:
                return int(self.x_filter.x_prev), int(self.y_filter.x_prev)
            return 0, 0

        # Initialize filters if first run
        if self.x_filter is None or self.y_filter is None:
            self.x_filter = OneEuroFilter(current_time, x, self._min_cutoff, self._beta)
            self.y_filter = OneEuroFilter(current_time, y, self._min_cutoff, self._beta)
            return int(round(x)), int(round(y))

        # 1. Apply 1 Euro Filter (Smoothing)
        smoothed_x = self.x_filter(current_time, x)
        smoothed_y = self.y_filter(current_time, y)

        # 2. Apply Velocity-based Prediction
        # Calculate velocity from filter's derivative state
        dx = self.x_filter.dx_prev
        dy = self.y_filter.dx_prev

        # Project future position
        # prediction_scale is effectively "how many seconds ahead to look"
        # but configured as a simple multiplier for UX
        # Realistically, reasonable values are 0.0 (off) to 0.2 (200ms)
        # But user config might use a larger arbitrary scale

        predicted_x = smoothed_x + (dx * self._prediction_scale * 0.1)
        predicted_y = smoothed_y + (dy * self._prediction_scale * 0.1)

        # 3. Safety Clamping & Validation
        if not math.isfinite(predicted_x):
            predicted_x = x
        if not math.isfinite(predicted_y):
            predicted_y = y

        return int(round(predicted_x)), int(round(predicted_y))

    def reset(self):
        """Reset filter state"""
        self.x_filter = None
        self.y_filter = None
