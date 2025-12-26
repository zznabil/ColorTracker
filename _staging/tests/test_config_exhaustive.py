import pytest

from utils.config import Config


@pytest.fixture
def clean_config():
    """Returns a clean config instance without loading from disk"""
    config = Config()
    # Reset to defaults manually just in case
    for key, schema in config.DEFAULT_CONFIG.items():
        setattr(config, key, schema["default"])
    return config


def test_exhaustive_type_validation(clean_config):
    """Test every field in DEFAULT_CONFIG with deliberately wrong types"""
    for key, schema in clean_config.DEFAULT_CONFIG.items():
        expected_type = schema["type"]

        # Try to inject a clearly wrong type (e.g., a complex object or list)
        bad_value = ["not", "a", "valid", "type"]

        corrected = clean_config.validate(key, bad_value)

        # Should either be the default or a successfully cast value (unlikely for list)
        if isinstance(corrected, expected_type):
            pass  # Success
        else:
            pytest.fail(f"Field '{key}' failed type validation. Expected {expected_type}, got {type(corrected)}")


def test_exhaustive_range_clamping(clean_config):
    """Test numeric fields with values outside their allowed min/max ranges"""
    for key, schema in clean_config.DEFAULT_CONFIG.items():
        if "min" in schema:
            # Inject way below min
            val_below = schema["min"] - 1000
            corrected = clean_config.validate(key, val_below)
            assert corrected >= schema["min"], (
                f"Field '{key}' failed min clamp. Got {corrected}, min is {schema['min']}"
            )

        if "max" in schema:
            # Inject way above max
            val_above = schema["max"] + 1000
            corrected = clean_config.validate(key, val_above)
            assert corrected <= schema["max"], (
                f"Field '{key}' failed max clamp. Got {corrected}, max is {schema['max']}"
            )


def test_exhaustive_options_validation(clean_config):
    """Test fields with specific options/enums for invalid choices"""
    for key, schema in clean_config.DEFAULT_CONFIG.items():
        if "options" in schema:
            bad_option = "DEFINITELY_NOT_A_VALID_OPTION_12345"
            corrected = clean_config.validate(key, bad_option)
            assert corrected == schema["default"], f"Field '{key}' allowed invalid option '{bad_option}'"


def test_type_casting_logic(clean_config):
    """Deep dive into specific type casting logic (e.g., bool strings)"""
    # Test Boolean Casting from strings
    assert clean_config.validate("enabled", "true") is True
    assert clean_config.validate("enabled", "1") is True
    assert clean_config.validate("enabled", "yes") is True
    assert clean_config.validate("enabled", "on") is True
    assert clean_config.validate("enabled", "false") is False
    assert clean_config.validate("enabled", "0") is False

    # Test Numeric Casting from strings
    assert clean_config.validate("fov_x", "100") == 100
    assert clean_config.validate("fov_x", "150.5") == 150  # Int cast
    assert clean_config.validate("smoothing", "5.5") == 5.5
