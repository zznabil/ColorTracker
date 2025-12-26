import math


class SimpleEMA:
    """
    Simple Exponential Moving Average filter.
    Fixed smoothing regardless of speed.
    """

    def __init__(self, alpha=0.5, x0=0.0):
        self.alpha = float(alpha)
        self.x_prev = float(x0)
        self.initialized = True if x0 != 0 else False

    def __call__(self, x):
        x_val = float(x)

        # Handle NaN/Inf recovery
        if not math.isfinite(x_val):
            return self.x_prev

        if not self.initialized or not math.isfinite(self.x_prev):
            self.x_prev = x_val
            self.initialized = True
            return self.x_prev

        x_hat = self.alpha * x_val + (1 - self.alpha) * self.x_prev
        self.x_prev = x_hat
        return x_hat


class MedianFilter:
    """
    Simple Moving Median filter.
    Highly effective at removing 'shot noise' or outlier detection glitches.
    """

    def __init__(self, window_size=3):
        self.window_size = window_size
        self.buffer = []

    def __call__(self, x):
        self.buffer.append(float(x))
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)

        temp = sorted(self.buffer)
        return temp[len(temp) // 2]


class DoubleEMA:
    """
    Double Exponential Moving Average (DEMA).
    Reduces lag by using two EMA layers.
    Formula: 2*EMA1 - EMA2(EMA1)
    """

    def __init__(self, alpha=0.5, x0=0.0):
        self.alpha = float(alpha)
        self.ema1 = SimpleEMA(alpha, x0)
        self.ema2 = SimpleEMA(alpha, x0)

    def __call__(self, x):
        e1 = self.ema1(x)
        e2 = self.ema2(e1)
        return 2 * e1 - e2


class TripleEMA:
    """
    Triple Exponential Moving Average (TEMA).
    The fastest EMA variant with minimal lag.
    Formula: 3*EMA1 - 3*EMA2 + EMA3
    """

    def __init__(self, alpha=0.5, x0=0.0):
        self.alpha = float(alpha)
        self.ema1 = SimpleEMA(alpha, x0)
        self.ema2 = SimpleEMA(alpha, x0)
        self.ema3 = SimpleEMA(alpha, x0)

    def __call__(self, x):
        e1 = self.ema1(x)
        e2 = self.ema2(e1)
        e3 = self.ema3(e2)
        return 3 * e1 - 3 * e2 + e3


class DynamicEMA:
    """
    EMA with an Alpha that scales based on speed/acceleration.
    Snappier during fast movement, smoother during slow movement.
    """

    def __init__(self, min_alpha=0.1, max_alpha=0.9, sensitivity=2.0, x0=0.0):
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        self.sensitivity = sensitivity
        self.x_prev = float(x0)
        self.initialized = False

    def __call__(self, x):
        x_val = float(x)

        # Handle NaN/Inf recovery
        if not math.isfinite(x_val):
            return self.x_prev

        if not self.initialized or not math.isfinite(self.x_prev):
            self.x_prev = x_val
            self.initialized = True
            return self.x_prev

        # Calculate speed/delta
        delta = abs(x_val - self.x_prev)

        # Scale alpha between min and max based on delta
        # If delta is large, alpha goes toward max_alpha (responsive)
        alpha = self.min_alpha + (self.max_alpha - self.min_alpha) * (
            1.0 - math.exp(-delta / (self.sensitivity + 0.01))
        )

        x_hat = alpha * x_val + (1 - alpha) * self.x_prev
        self.x_prev = x_hat
        return x_hat
