import time

import pytest

from core.prediction import PredictionSystem
from utils.config import Config


@pytest.fixture
def pred_sys():
    config = Config()
    config.prediction_enabled = True
    config.prediction_multiplier = 1.0
    return PredictionSystem(config)


def test_prediction_methods_switch(pred_sys):
    """Verify that switching filter methods correctly initializes different filters"""
    methods = ["EMA", "DEMA", "TEMA", "Median+EMA", "Dynamic EMA"]

    for method in methods:
        pred_sys.config.filter_method = method
        pred_sys.filter_x = None  # Force reset

        # First call initializes
        pred_sys.predict(100, 100)

        assert pred_sys.filter_x is not None
        # Check if it's the right type
        if method == "EMA":
            from utils.filters import SimpleEMA

            assert isinstance(pred_sys.filter_x, SimpleEMA)
        elif method == "DEMA":
            from utils.filters import DoubleEMA

            assert isinstance(pred_sys.filter_x, DoubleEMA)


def test_prediction_disabled(pred_sys):
    """When prediction is disabled, output should closely follow input (after filtering)"""
    pred_sys.config.prediction_enabled = False
    pred_sys.config.smoothing = 0.0  # Instant tracking

    # Initialize
    pred_sys.predict(100, 100)
    time.sleep(0.01)

    # Move target
    x, y = pred_sys.predict(200, 200)

    # Without prediction, it should just be the filtered (instant) position
    assert x == 200
    assert y == 200


def test_prediction_velocity_lead(pred_sys):
    """Verify that prediction 'leads' the target based on velocity"""
    pred_sys.config.prediction_enabled = True
    pred_sys.config.prediction_multiplier = 1.0
    pred_sys.config.smoothing = 0.0

    # Call 1: Initialize at 100
    pred_sys.predict(100, 100)
    time.sleep(0.05)  # Small dt

    # Call 2: Move to 110. Velocity is +10 per ~0.05s
    # Predicted position should be > 110
    x, y = pred_sys.predict(110, 110)

    assert x > 110
    assert y > 110


def test_reset_functionality(pred_sys):
    """Verify reset clears state"""
    pred_sys.predict(100, 100)
    assert pred_sys.filter_x is not None

    pred_sys.reset()
    assert pred_sys.filter_x is None
    assert pred_sys.prev_x == 0
