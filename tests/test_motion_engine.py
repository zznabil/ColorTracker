"""
Unit tests for the Motion Engine (1 Euro Filter + Prediction)
"""

import time

import pytest

from core.motion_engine import MotionEngine


class MockConfig:
    def __init__(self):
        self.motion_min_cutoff = 0.05
        self.motion_beta = 0.05
        self.prediction_scale = 1.0


@pytest.fixture
def motion_engine():
    config = MockConfig()
    return MotionEngine(config)


def test_initialization(motion_engine):
    """Test that the engine initializes with correct default values"""
    assert motion_engine._min_cutoff == 0.05
    assert motion_engine._beta == 0.05
    assert motion_engine._prediction_scale == 1.0
    assert motion_engine.x_filter is None
    assert motion_engine.y_filter is None


def test_static_input_convergence(motion_engine):
    """Test that a constant input converges to the value (smoothing test)"""
    # First frame initializes filters
    x, y = 100, 100
    out_x, out_y = motion_engine.process(x, y, 0.016)
    assert out_x == 100
    assert out_y == 100

    # Subsequent frames with same input should stay 100
    for _ in range(10):
        time.sleep(0.001)  # Advance time slightly
        out_x, out_y = motion_engine.process(x, y, 0.016)
        # Should remain exactly 100 as dx is 0
        assert out_x == 100
        assert out_y == 100


def test_motion_smoothing(motion_engine):
    """Test that moving input is smoothed (output starts behind input)"""
    # Disable prediction to test pure smoothing
    motion_engine.config.prediction_scale = 0.0
    motion_engine.update_config()

    # Initialize at 0,0
    motion_engine.process(0, 0, 0.016)

    # Move slowly (simulate time passing)
    time.sleep(0.016)
    out_x, out_y = motion_engine.process(1, 1, 0.016)

    # With prediction disabled, filtered value should be significantly less than 1
    # 1Euro filter with low cutoff lags behind.
    assert out_x < 1 or out_y < 1


def test_prediction_logic(motion_engine):
    """Test that prediction projects targets forward"""
    # Config for stronger prediction to be obvious
    motion_engine.config.prediction_scale = 2.0
    motion_engine.update_config()

    # 0 -> 10 -> 20 (Constant velocity)
    t0 = time.perf_counter()
    motion_engine.process(0, 0, 0.016)

    # Wait and move to 10
    while time.perf_counter() - t0 < 0.016:
        pass
    motion_engine.process(10, 0, 0.016)

    # Wait and move to 20
    while time.perf_counter() - t0 < 0.032:
        pass
    out_x, out_y = motion_engine.process(20, 0, 0.016)

    # Input is 20. Velocity is +ve. Prediction should add to it.
    # So output > 20.
    assert out_x > 20


def test_robustness_nan(motion_engine):
    """Test handling of NaN values"""
    motion_engine.process(10, 10, 0.016)

    # Force filters to exist
    assert motion_engine.x_filter is not None

    out_x, out_y = motion_engine.process(float("nan"), float("nan"), 0.016)

    # Should return previous valid (10) or clamped value, but definitely strict int
    assert isinstance(out_x, int)
    assert isinstance(out_y, int)

    # Based on implementation, if x is NaN, it returns previous filter value
    assert out_x == 10
    assert out_y == 10


def test_config_update(motion_engine):
    """Test dynamic config updates"""
    motion_engine.config.motion_min_cutoff = 0.5
    motion_engine.config.motion_beta = 0.8
    motion_engine.config.prediction_scale = 0.0

    # Should not update immediately
    assert motion_engine._min_cutoff == 0.05

    # Update
    motion_engine.update_config()
    assert motion_engine._min_cutoff == 0.5
    assert motion_engine._beta == 0.8
    assert motion_engine._prediction_scale == 0.0
