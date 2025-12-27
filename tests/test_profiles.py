import os
import shutil

import pytest

from utils.config import Config


@pytest.fixture
def profile_config():
    """Fixture that uses a temporary profiles directory"""
    # Create a fresh instance
    config = Config()
    # Use a temp dir for testing
    test_profiles_dir = "tests/temp_profiles"
    config.profiles_dir = test_profiles_dir

    if os.path.exists(test_profiles_dir):
        shutil.rmtree(test_profiles_dir)
    os.makedirs(test_profiles_dir)

    yield config

    # Cleanup
    if os.path.exists(test_profiles_dir):
        shutil.rmtree(test_profiles_dir)

def test_profile_lifecycle(profile_config):
    # 1. Ensure empty initially
    assert profile_config.get_profiles() == []

    # 2. Save a profile
    profile_config.fov_x = 123
    profile_config.save_profile("test_profile")

    assert "test_profile" in profile_config.get_profiles()
    assert os.path.exists(os.path.join(profile_config.profiles_dir, "test_profile.json"))

    # 3. Modify state
    profile_config.fov_x = 50
    assert profile_config.fov_x == 50

    # 4. Load profile
    profile_config.load_profile("test_profile")
    assert profile_config.fov_x == 123

    # 5. Delete profile
    profile_config.delete_profile("test_profile")
    assert "test_profile" not in profile_config.get_profiles()
    assert not os.path.exists(os.path.join(profile_config.profiles_dir, "test_profile.json"))

def test_invalid_profile_name(profile_config):
    with pytest.raises(ValueError):
        profile_config.save_profile("")

    with pytest.raises(ValueError):
        profile_config.save_profile("   ")
