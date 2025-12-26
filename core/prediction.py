#!/usr/bin/env python3

"""
Prediction System Module

Handles velocity-based prediction for target movement using EMA-based filters.
"""

import os
import sys
import time
from typing import Any

# Add root to path to ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.filters import DoubleEMA, DynamicEMA, MedianFilter, SimpleEMA, TripleEMA


class PredictionSystem:
    """Handles predictive tracking using EMA-based filtering"""

    # Explicitly declare dynamic attributes for static analysis
    filter_x: Any
    filter_y: Any
    _filter_method: str
    _smoothing: float
    _prediction_enabled: bool
    _prediction_multiplier: float

    def __init__(self, config):
        """
        Initialize the prediction system
        """
        self.config = config
        self.prev_x = 0
        self.prev_y = 0
        self.velocity_x = 0
        self.velocity_y = 0
        self.last_time = 0
        self.filter_x = None
        self.filter_y = None

        # Initialize cached config values
        self.update_config()

    def update_config(self):
        """Update cached configuration values to avoid getattr overhead in hot loop"""
        cfg = self.config
        self._filter_method = getattr(cfg, "filter_method", "EMA")
        self._smoothing = getattr(cfg, "smoothing", 2.0)
        self._prediction_enabled = getattr(cfg, "prediction_enabled", True)
        self._prediction_multiplier = getattr(cfg, "prediction_multiplier", 0.5)

    def predict(self, target_x: int, target_y: int) -> tuple[int, int]:
        """
        Predict the future position of the target using EMA filtering.
        Optimized for ultra-high FPS performance.
        """
        current_time = time.perf_counter()

        # Use cached config values
        filter_method = self._filter_method
        smoothing = self._smoothing
        prediction_enabled = self._prediction_enabled
        multiplier = self._prediction_multiplier

        # 1. Select and initialize filters if needed
        smooth_x: float = float(target_x)
        smooth_y: float = float(target_y)

        # Optimized filter selection with reduced overhead
        if filter_method == "EMA":
            if not isinstance(self.filter_x, SimpleEMA):
                alpha = 1.0 / (max(0.0, smoothing) + 1.0)
                self.filter_x = SimpleEMA(alpha=alpha, x0=target_x)
                self.filter_y = SimpleEMA(alpha=alpha, x0=target_y)
                self.last_time = current_time
                self.prev_x = float(target_x)
                self.prev_y = float(target_y)

            alpha = 1.0 / (max(0.0, smoothing) + 1.0)
            if isinstance(self.filter_x, SimpleEMA) and isinstance(self.filter_y, SimpleEMA):
                self.filter_x.alpha = alpha
                self.filter_y.alpha = alpha
                smooth_x = float(self.filter_x(target_x))
                smooth_y = float(self.filter_y(target_y))

        elif filter_method == "Median+EMA":
            if not isinstance(self.filter_x, tuple) or len(self.filter_x) != 2:
                alpha = 1.0 / (max(0.0, smoothing) + 1.0)
                self.filter_x = (MedianFilter(3), SimpleEMA(alpha=alpha, x0=target_x))
                self.filter_y = (MedianFilter(3), SimpleEMA(alpha=alpha, x0=target_y))
                self.last_time = current_time
                self.prev_x = float(target_x)
                self.prev_y = float(target_y)

            alpha = 1.0 / (max(0.0, smoothing) + 1.0)
            mf_x, ema_x = self.filter_x
            mf_y, ema_y = self.filter_y

            if isinstance(ema_x, SimpleEMA) and isinstance(ema_y, SimpleEMA):
                ema_x.alpha = alpha
                ema_y.alpha = alpha

            if (
                isinstance(mf_x, MedianFilter)
                and isinstance(mf_y, MedianFilter)
                and isinstance(ema_x, SimpleEMA)
                and isinstance(ema_y, SimpleEMA)
            ):
                smooth_x = float(ema_x(mf_x(target_x)))
                smooth_y = float(ema_y(mf_y(target_y)))

        elif filter_method == "Dynamic EMA":
            if not isinstance(self.filter_x, DynamicEMA):
                self.filter_x = DynamicEMA(min_alpha=0.01, max_alpha=1.0, sensitivity=max(0.0, smoothing), x0=target_x)
                self.filter_y = DynamicEMA(min_alpha=0.01, max_alpha=1.0, sensitivity=max(0.0, smoothing), x0=target_y)
                self.last_time = current_time
                self.prev_x = float(target_x)
                self.prev_y = float(target_y)

            if isinstance(self.filter_x, DynamicEMA) and isinstance(self.filter_y, DynamicEMA):
                self.filter_x.sensitivity = max(0.0, smoothing)
                self.filter_y.sensitivity = max(0.0, smoothing)
                smooth_x = float(self.filter_x(target_x))
                smooth_y = float(self.filter_y(target_y))

        elif filter_method == "DEMA":
            if not isinstance(self.filter_x, DoubleEMA):
                alpha = 1.0 / (max(0.0, smoothing) + 1.0)
                self.filter_x = DoubleEMA(alpha=alpha, x0=target_x)
                self.filter_y = DoubleEMA(alpha=alpha, x0=target_y)
                self.last_time = current_time
                self.prev_x = float(target_x)
                self.prev_y = float(target_y)

            alpha = 1.0 / (max(0.0, smoothing) + 1.0)
            if isinstance(self.filter_x, DoubleEMA) and isinstance(self.filter_y, DoubleEMA):
                self.filter_x.ema1.alpha = alpha
                self.filter_x.ema2.alpha = alpha
                self.filter_y.ema1.alpha = alpha
                self.filter_y.ema2.alpha = alpha
                smooth_x = float(self.filter_x(target_x))
                smooth_y = float(self.filter_y(target_y))

        elif filter_method == "TEMA":
            if not isinstance(self.filter_x, TripleEMA):
                alpha = 1.0 / (max(0.0, smoothing) + 1.0)
                self.filter_x = TripleEMA(alpha=alpha, x0=target_x)
                self.filter_y = TripleEMA(alpha=alpha, x0=target_y)
                self.last_time = current_time
                self.prev_x = float(target_x)
                self.prev_y = float(target_y)

            alpha = 1.0 / (max(0.0, smoothing) + 1.0)
            if isinstance(self.filter_x, TripleEMA) and isinstance(self.filter_y, TripleEMA):
                self.filter_x.ema1.alpha = alpha
                self.filter_x.ema2.alpha = alpha
                self.filter_x.ema3.alpha = alpha
                self.filter_y.ema1.alpha = alpha
                self.filter_y.ema2.alpha = alpha
                self.filter_y.ema3.alpha = alpha
                smooth_x = float(self.filter_x(target_x))
                smooth_y = float(self.filter_y(target_y))

        else:  # Fallback to EMA
            if not isinstance(self.filter_x, SimpleEMA):
                alpha = 1.0 / (max(0.0, smoothing) + 1.0)
                self.filter_x = SimpleEMA(alpha=alpha, x0=target_x)
                self.filter_y = SimpleEMA(alpha=alpha, x0=target_y)
                self.last_time = current_time
                self.prev_x = float(target_x)
                self.prev_y = float(target_y)
            if isinstance(self.filter_x, SimpleEMA) and isinstance(self.filter_y, SimpleEMA):
                smooth_x = float(self.filter_x(target_x))
                smooth_y = float(self.filter_y(target_y))

        # 2. Calculate dt (optimized)
        dt = current_time - self.last_time
        if dt <= 0:
            dt = 0.001
        dt = min(dt, 0.1)

        # 3. Calculate Velocity from SMOOTHED positions
        self.velocity_x = (smooth_x - self.prev_x) / dt
        self.velocity_y = (smooth_y - self.prev_y) / dt

        # 4. Apply Prediction
        if prediction_enabled:
            pred_x = smooth_x + self.velocity_x * (dt * multiplier)
            pred_y = smooth_y + self.velocity_y * (dt * multiplier)
        else:
            pred_x = smooth_x
            pred_y = smooth_y

        # Store state
        self.prev_x = smooth_x
        self.prev_y = smooth_y
        self.last_time = current_time

        return round(pred_x), round(pred_y)

    def reset(self):
        """Reset the prediction system state"""
        self.prev_x = 0
        self.prev_y = 0
        self.velocity_x = 0
        self.velocity_y = 0
        self.last_time = 0
        self.filter_x = None
        self.filter_y = None
