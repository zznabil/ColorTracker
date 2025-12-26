import pytest

from utils.filters import DynamicEMA, MedianFilter, SimpleEMA, TripleEMA


def test_ema_zero_alpha():
    """Ensure EMA behaves reasonably even if alpha is near zero (extreme smoothing)"""
    ema = SimpleEMA(alpha=0.000001, x0=100)
    v = ema(200)
    assert 100 <= v <= 101  # Should barely move


def test_ema_high_alpha():
    """Ensure EMA tracks instantly if alpha is 1.0"""
    ema = SimpleEMA(alpha=1.0, x0=100)
    v = ema(200)
    assert v == 200


def test_median_filter_extremes():
    """Test MedianFilter with window edge cases"""
    # Smallest window
    m1 = MedianFilter(window_size=1)
    assert m1(50) == 50
    assert m1(100) == 100

    # Even window (median usually picks middle or average, implementation specific)
    m2 = MedianFilter(window_size=2)
    m2(10)
    assert m2(20) in [10, 15, 20]  # Depends on np.median behavior


def test_filter_empty_initialization():
    """Ensure filters handle first-call initialization without crashing"""
    ema = SimpleEMA(alpha=0.5)  # No x0
    assert ema(100) == 100

    de = DynamicEMA()
    assert de(100) == 100


def test_triple_ema_convergence():
    """Triple EMA should eventually converge on a static target"""
    tema = TripleEMA(alpha=0.5, x0=0)
    for _ in range(50):
        val = tema(100)
    assert pytest.approx(val, rel=1e-2) == 100


def test_dynamic_ema_sensitivity_extremes():
    """Dynamic EMA with 0 sensitivity should act like a static EMA"""
    de = DynamicEMA(min_alpha=0.5, max_alpha=0.5, sensitivity=0.0)
    de(100)
    v2 = de(200)
    assert v2 == 150  # Static 0.5 EMA
