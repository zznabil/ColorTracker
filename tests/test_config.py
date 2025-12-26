import json
import os

import pytest

from utils.config import Config


@pytest.fixture
def temp_config_file():
    """Fixture to manage a temporary config file for testing"""
    test_file = "config_pytest_tmp.json"

    # Setup data
    currupt_data = {
        "fov_x": "corrupted_string",
        "motion_min_cutoff": -500.0,
        "target_fps": 9999,
        "aim_point": "InvalidTarget",
    }

    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(currupt_data, f)

    yield test_file

    # Teardown
    if os.path.exists(test_file):
        os.remove(test_file)


def test_config_self_healing(temp_config_file):
    """Test that Config class correctly repairs corrupted values upon loading"""
    config = Config()
    config.config_file = temp_config_file
    config.load()

    # Checks
    assert config.fov_x == 50  # String should reset to default
    assert config.motion_min_cutoff == 0.001  # -500 should clamp to min
    assert config.target_fps == 1000  # 9999 should clamp to max
    assert config.aim_point == 1  # Invalid option should reset to default (Body=1)
