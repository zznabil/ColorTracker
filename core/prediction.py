#!/usr/bin/env python3

"""
Prediction System Module

Handles velocity-based prediction for target movement using EMA-based filters.
Optimization: Refactored to avoid dispatch overhead in hot path.
"""

import os
import sys
import time
from collections.abc import Callable
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
    _apply_filter: Callable[[float, float, float, float], tuple[float, float]]

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

        # Initialize cached config values and strategy
        self._last_filter_method = None
        self.update_config()

    def update_config(self):
        """Update cached configuration values to avoid getattr overhead in hot loop"""
        cfg = self.config
        self._filter_method = getattr(cfg, "filter_method", "EMA")
        self._smoothing = getattr(cfg, "smoothing", 2.0)
        self._prediction_enabled = getattr(cfg, "prediction_enabled", True)
        self._prediction_multiplier = getattr(cfg, "prediction_multiplier", 0.5)

        # Update filter strategy if method changed
        if self._filter_method != self._last_filter_method:
             self._update_filter_strategy()
             self._last_filter_method = self._filter_method

    def _update_filter_strategy(self):
        """Sets the filter application strategy based on configuration"""
        method = self._filter_method

        if method == "EMA":
            self._apply_filter = self._apply_ema
        elif method == "Median+EMA":
             self._apply_filter = self._apply_median_ema
        elif method == "Dynamic EMA":
             self._apply_filter = self._apply_dynamic_ema
        elif method == "DEMA":
             self._apply_filter = self._apply_dema
        elif method == "TEMA":
             self._apply_filter = self._apply_tema
        else:
             self._apply_filter = self._apply_ema

        # Reset filters when strategy changes
        self.filter_x = None
        self.filter_y = None

    def _apply_ema(self, tx: float, ty: float, smoothing: float, current_time: float) -> tuple[float, float]:
        if not isinstance(self.filter_x, SimpleEMA):
            alpha = 1.0 / (max(0.0, smoothing) + 1.0)
            self.filter_x = SimpleEMA(alpha=alpha, x0=tx)
            self.filter_y = SimpleEMA(alpha=alpha, x0=ty)
            # Initialize history
            self.prev_x = tx
            self.prev_y = ty
            self.last_time = current_time

        alpha = 1.0 / (max(0.0, smoothing) + 1.0)
        # We can assume they are SimpleEMA because we reset filters on strategy change
        self.filter_x.alpha = alpha
        self.filter_y.alpha = alpha
        return float(self.filter_x(tx)), float(self.filter_y(ty))

    def _apply_median_ema(self, tx: float, ty: float, smoothing: float, current_time: float) -> tuple[float, float]:
        if not isinstance(self.filter_x, tuple):
            alpha = 1.0 / (max(0.0, smoothing) + 1.0)
            self.filter_x = (MedianFilter(3), SimpleEMA(alpha=alpha, x0=tx))
            self.filter_y = (MedianFilter(3), SimpleEMA(alpha=alpha, x0=ty))
            self.prev_x = tx
            self.prev_y = ty
            self.last_time = current_time

        alpha = 1.0 / (max(0.0, smoothing) + 1.0)
        mf_x, ema_x = self.filter_x
        mf_y, ema_y = self.filter_y

        ema_x.alpha = alpha
        ema_y.alpha = alpha

        return float(ema_x(mf_x(tx))), float(ema_y(mf_y(ty)))

    def _apply_dynamic_ema(self, tx: float, ty: float, smoothing: float, current_time: float) -> tuple[float, float]:
        if not isinstance(self.filter_x, DynamicEMA):
            self.filter_x = DynamicEMA(min_alpha=0.01, max_alpha=1.0, sensitivity=max(0.0, smoothing), x0=tx)
            self.filter_y = DynamicEMA(min_alpha=0.01, max_alpha=1.0, sensitivity=max(0.0, smoothing), x0=ty)
            self.prev_x = tx
            self.prev_y = ty
            self.last_time = current_time

        self.filter_x.sensitivity = max(0.0, smoothing)
        self.filter_y.sensitivity = max(0.0, smoothing)
        return float(self.filter_x(tx)), float(self.filter_y(ty))

    def _apply_dema(self, tx: float, ty: float, smoothing: float, current_time: float) -> tuple[float, float]:
        if not isinstance(self.filter_x, DoubleEMA):
            alpha = 1.0 / (max(0.0, smoothing) + 1.0)
            self.filter_x = DoubleEMA(alpha=alpha, x0=tx)
            self.filter_y = DoubleEMA(alpha=alpha, x0=ty)
            self.prev_x = tx
            self.prev_y = ty
            self.last_time = current_time

        alpha = 1.0 / (max(0.0, smoothing) + 1.0)
        self.filter_x.ema1.alpha = alpha
        self.filter_x.ema2.alpha = alpha
        self.filter_y.ema1.alpha = alpha
        self.filter_y.ema2.alpha = alpha
        return float(self.filter_x(tx)), float(self.filter_y(ty))

    def _apply_tema(self, tx: float, ty: float, smoothing: float, current_time: float) -> tuple[float, float]:
        if not isinstance(self.filter_x, TripleEMA):
            alpha = 1.0 / (max(0.0, smoothing) + 1.0)
            self.filter_x = TripleEMA(alpha=alpha, x0=tx)
            self.filter_y = TripleEMA(alpha=alpha, x0=ty)
            self.prev_x = tx
            self.prev_y = ty
            self.last_time = current_time

        alpha = 1.0 / (max(0.0, smoothing) + 1.0)
        self.filter_x.ema1.alpha = alpha
        self.filter_x.ema2.alpha = alpha
        self.filter_x.ema3.alpha = alpha
        self.filter_y.ema1.alpha = alpha
        self.filter_y.ema2.alpha = alpha
        self.filter_y.ema3.alpha = alpha
        return float(self.filter_x(tx)), float(self.filter_y(ty))

    def predict(self, target_x: int, target_y: int) -> tuple[int, int]:
        """
        Predict the future position of the target using EMA filtering.
        Optimized for ultra-high FPS performance.
        """
        current_time = time.perf_counter()

        # 1. Select and initialize filters if needed
        # Dispatch to the pre-selected strategy
        smooth_x, smooth_y = self._apply_filter(float(target_x), float(target_y), self._smoothing, current_time)

        # 2. Calculate dt (optimized)
        dt = current_time - self.last_time
        if dt <= 0:
            dt = 0.001
        dt = min(dt, 0.1)

        # 3. Calculate Velocity from SMOOTHED positions
        self.velocity_x = (smooth_x - self.prev_x) / dt
        self.velocity_y = (smooth_y - self.prev_y) / dt

        # 4. Apply Prediction
        if self._prediction_enabled:
            pred_x = smooth_x + self.velocity_x * (dt * self._prediction_multiplier)
            pred_y = smooth_y + self.velocity_y * (dt * self._prediction_multiplier)
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
