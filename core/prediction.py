#!/usr/bin/env python3

"""
Prediction System Module

Handles velocity-based prediction for target movement using 1 Euro Filter.
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

    def predict(self, target_x: int, target_y: int) -> tuple[int, int]:
        """
        Predict the future position of the target using EMA filtering.
        """
        current_time = time.time()
        filter_method = getattr(self.config, "filter_method", "EMA")
        smoothing = getattr(self.config, "smoothing", 2.0)

        # 1. Select and initialize filters if needed
        smooth_x: float = float(target_x)
        smooth_y: float = float(target_y)

        if filter_method == "EMA":
            if not isinstance(self.filter_x, SimpleEMA):
                alpha = 1.0 / (max(0.0, smoothing) + 1.0)
                self.filter_x = SimpleEMA(alpha=alpha, x0=target_x)
                self.filter_y = SimpleEMA(alpha=alpha, x0=target_y)
                self.last_time = current_time
                self.prev_x = float(target_x)
                self.prev_y = float(target_y)

            alpha = 1.0 / (max(0.1, smoothing) + 1.0)
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

            alpha = 1.0 / (max(0.1, smoothing) + 1.0)
            # Access tuple elements safely for static analysis
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
                self.filter_x = DynamicEMA(min_alpha=0.01, max_alpha=0.8, sensitivity=smoothing, x0=target_x)
                self.filter_y = DynamicEMA(min_alpha=0.01, max_alpha=0.8, sensitivity=smoothing, x0=target_y)
                self.last_time = current_time
                self.prev_x = float(target_x)
                self.prev_y = float(target_y)

            if isinstance(self.filter_x, DynamicEMA) and isinstance(self.filter_y, DynamicEMA):
                self.filter_x.sensitivity = smoothing
                self.filter_y.sensitivity = smoothing
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

            alpha = 1.0 / (max(0.1, smoothing) + 1.0)
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

            alpha = 1.0 / (max(0.1, smoothing) + 1.0)
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

        # 2. Calculate dt
        dt = current_time - self.last_time
        if dt <= 0:
            dt = 0.001
        dt = min(dt, 0.1)

        # 3. Calculate Velocity from SMOOTHED positions
        self.velocity_x = (smooth_x - self.prev_x) / dt
        self.velocity_y = (smooth_y - self.prev_y) / dt

        # 4. Apply Prediction
        multiplier = getattr(self.config, "prediction_multiplier", 0.5)

        if getattr(self.config, "prediction_enabled", True):
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
