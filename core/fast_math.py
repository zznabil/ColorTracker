"""
Fast Math Kernel (Phase 6: Bare Metal Performance)

Optimized mathematical functions compiled with Numba JIT for
extreme performance in the tracking hot loop.
"""

import math

try:
    from numba import jit

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

    # Fallback decorator if Numba is not available
    def jit(nopython=True, cache=True, fastmath=True):
        def decorator(func):
            return func

        return decorator


# Constants
TWO_PI = 6.283185307179586


@jit(nopython=True, cache=True, fastmath=True)
def one_euro_filter_step(
    t: float,
    x: float,
    min_cutoff: float,
    beta: float,
    d_cutoff: float,
    value_prev: float,
    deriv_prev: float,
    t_prev: float,
) -> tuple[float, float, float]:
    """
    Stateless 1 Euro Filter step.

    Args:
        t: Current timestamp
        x: Current noisy value
        min_cutoff: Minimum cutoff frequency
        beta: Speed coefficient
        d_cutoff: Derivative cutoff
        value_prev: Previous filtered value
        deriv_prev: Previous filtered derivative
        t_prev: Previous timestamp

    Returns:
        (x_hat, dx_hat, t) - New filtered value, new derivative, and current timestamp
    """
    t_e = t - t_prev

    # Avoid divide by zero / backward time jumps
    if t_e <= 0.0:
        return value_prev, deriv_prev, t_prev

    # 1. Calculate the filtered derivative of the signal
    # r_d = 2 * pi * d_cutoff * t_e
    r_d = TWO_PI * d_cutoff * t_e
    a_d = r_d / (r_d + 1.0)

    dx = (x - value_prev) / t_e
    dx_hat = a_d * dx + (1.0 - a_d) * deriv_prev

    # 2. Calculate the filtered signal
    cutoff = min_cutoff + beta * abs(dx_hat)
    r = TWO_PI * cutoff * t_e
    a = r / (r + 1.0)

    x_hat = a * x + (1.0 - a) * value_prev

    return x_hat, dx_hat, t


@jit(nopython=True, cache=True, fastmath=True)
def calculate_prediction(
    dx: float,
    dy: float,
    prev_dx: float,
    prev_dy: float,
    dt: float,
    prediction_scale: float,
    smoothed_x: float,
    smoothed_y: float,
    screen_width: float,
    screen_height: float,
    fov_x: float,
    fov_y: float,
) -> tuple[float, float]:
    """
    Calculate predicted position with advanced physics logic.
    INCLUDES FIX for Axis-Coupling Bug (treating X/Y flips independently).
    """

    # 1. Velocity Magnitude (Chebyshev distance for speed)
    # Using max(abs(dx), abs(dy)) is faster than sqrt and sufficient for gating
    vel_mag = max(abs(dx), abs(dy))

    # 2. Velocity Gate
    vel_scale = 1.0
    if vel_mag < 100.0:
        vel_scale = max(0.0, vel_mag * 0.01)

    base_lookahead = 0.1 * prediction_scale * vel_scale

    # 3. Decoupled Direction Flip Suppression (FIXED)
    lookahead_x = base_lookahead
    lookahead_y = base_lookahead

    # If velocity flipped on X axis, zero out X prediction only
    if dx * prev_dx < 0:
        lookahead_x = 0.0

    # If velocity flipped on Y axis, zero out Y prediction only
    if dy * prev_dy < 0:
        lookahead_y = 0.0

    # 4. Apply Lookahead
    off_x = dx * lookahead_x
    off_y = dy * lookahead_y

    # 5. Adaptive Clamping logic
    # Calculate offset magnitude
    offset_sq = off_x * off_x + off_y * off_y

    # Dynamic limit based on FOV
    # max_offset = max(10.0, min(fov_x * 1.5, screen_width * 0.08))
    limit_a = fov_x * 1.5
    limit_b = screen_width * 0.08
    max_offset = 10.0
    if limit_a < limit_b:
        if limit_a > max_offset:
            max_offset = limit_a
    else:
        if limit_b > max_offset:
            max_offset = limit_b

    max_offset_sq = max_offset * max_offset

    # Clamp if offset exceeds limit
    if offset_sq > max_offset_sq:
        offset_mag = math.sqrt(offset_sq)
        scale = max_offset / offset_mag
        off_x *= scale
        off_y *= scale

    # 6. Apply to smoothed position
    pred_x = smoothed_x + off_x
    pred_y = smoothed_y + off_y

    # 7. Screen Clamping
    if pred_x < 0.0:
        pred_x = 0.0
    elif pred_x > screen_width - 1.0:
        pred_x = screen_width - 1.0

    if pred_y < 0.0:
        pred_y = 0.0
    elif pred_y > screen_height - 1.0:
        pred_y = screen_height - 1.0

    return pred_x, pred_y
