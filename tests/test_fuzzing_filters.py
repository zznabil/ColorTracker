import numpy as np

from utils.filters import DynamicEMA, SimpleEMA, TripleEMA


def test_ema_with_nan_and_inf():
    """Ensure filters don't crash when encountering Poison values like NaN or Inf"""
    ema = SimpleEMA(x0=100)

    # NaN check (should return last valid value: 100.0)
    res_nan = ema(float("nan"))
    assert res_nan == 100.0

    # Recover from NaN (should continue from 100.0)
    res_rec = ema(200)
    assert res_rec == 150.0  # (0.5 * 200) + (0.5 * 100)


def test_fuzzing_noise_tolerance():
    """Stress test DynamicEMA with randomized Gaussian noise"""
    de = DynamicEMA(min_alpha=0.1, max_alpha=0.9)

    # Generate 1000 noisy samples around center 100
    noise = np.random.normal(100, 50, 1000)

    for val in noise:
        res = de(val)
        # Verify result is always a finite float
        assert np.isfinite(res)
        assert isinstance(res, float)


def test_infinite_alpha_stability():
    """Test TripleEMA with extreme alpha values"""
    # Alpha > 1.0 (unstable but tests math robustness)
    tema = TripleEMA(alpha=2.0)
    res = tema(100)
    assert np.isfinite(res)

    # Alpha = 0
    tema2 = TripleEMA(alpha=0.0, x0=50)
    assert tema2(100) == 50  # Should never move
