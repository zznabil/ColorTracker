import json
import os

import pytest

from utils.config import Config


@pytest.fixture
def clean_profiles_dir():
    """Ensure profiles directory is clean before and after tests"""
    profiles_dir = "profiles"
    if not os.path.exists(profiles_dir):
        os.makedirs(profiles_dir)

    # Clean existing
    for f in os.listdir(profiles_dir):
        if f.endswith(".json") and f != "default.json":
             os.remove(os.path.join(profiles_dir, f))

    # Reset default profile to ensure clean state
    default_path = os.path.join(profiles_dir, "default.json")
    if os.path.exists(default_path):
        os.remove(default_path)

    yield profiles_dir

    # Cleanup
    for f in os.listdir(profiles_dir):
        if f.endswith(".json") and f != "default.json":
             os.remove(os.path.join(profiles_dir, f))

def test_list_profiles(clean_profiles_dir):
    config = Config() # Creates default.json
    profiles = config.list_profiles()
    assert "default" in profiles

    # Create a new profile manually
    simple_config = {"fov_x": 100}
    with open(os.path.join(clean_profiles_dir, "test_profile.json"), "w") as f:
        json.dump(simple_config, f)

    profiles = config.list_profiles()
    assert "test_profile" in profiles
    assert "default" in profiles

def test_save_and_load_profile(clean_profiles_dir):
    config = Config()

    # Capture initial value (whatever came from default/root config)
    initial_fov = config.fov_x

    # Save as new profile immediately so we don't dirty default
    success = config.save_profile("custom_aim")
    assert success
    assert config.current_profile_name == "custom_aim"

    # Change a setting in the NEW profile
    new_fov = initial_fov + 10
    config.update("fov_x", new_fov)
    assert config.fov_x == new_fov

    # Load default back
    config.load("default")
    assert config.current_profile_name == "default"
    assert config.fov_x == initial_fov # Should still be original

    # Load custom again
    config.load("custom_aim")
    assert config.current_profile_name == "custom_aim"
    assert config.fov_x == new_fov

def test_delete_profile(clean_profiles_dir):
    config = Config()
    config.save_profile("to_delete")

    assert "to_delete" in config.list_profiles()

    success = config.delete_profile("to_delete")
    assert success
    assert "to_delete" not in config.list_profiles()

    # Should automatically switch to default if current was deleted
    assert config.current_profile_name == "default"

def test_cannot_delete_default(clean_profiles_dir):
    config = Config()
    success = config.delete_profile("default")
    assert not success
    assert "default" in config.list_profiles()
