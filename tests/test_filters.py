from utils.filters import DynamicEMA, MedianFilter, SimpleEMA


def test_simple_ema_basic():
    """Test that SimpleEMA correctly calculates weighted averages"""
    ema = SimpleEMA(alpha=0.5)
    v1 = ema(100)
    v2 = ema(200)
    assert v1 == 100
    assert v2 == 150


def test_median_filter_outliers():
    """Test that MedianFilter correctly handles spikes/outliers"""
    median = MedianFilter(window_size=3)
    median(10)
    median(100)
    v = median(20)
    assert v == 20


def test_dynamic_ema_flow():
    """Test that DynamicEMA runs without error and progresses"""
    de = DynamicEMA(min_alpha=0.1, max_alpha=0.9, sensitivity=1.0)
    v1 = de(100)
    v2 = de(101)
    v3 = de(500)
    assert v1 == 100
    assert v2 > v1  # Should trend upwards
    assert v3 > v2
