import json
import os
from unittest.mock import patch

import pytest

from utils.config import Config


@pytest.fixture
def clean_config(tmp_path):
    """Create a Config instance with a temporary file path."""
    # Patch get_app_dir to return tmp_path
    with patch("utils.paths.get_app_dir", return_value=str(tmp_path)):
        config = Config()
        # Ensure we start with a clean state
        config.config_file = str(tmp_path / "config.json")
        # Save initial defaults
        config.save()
        return config


def test_reset_to_defaults(clean_config):
    """Test complete reset to defaults."""
    # Modify some values (within valid ranges)
    clean_config.update("fov_x", 400)
    clean_config.update("target_color", 0xFFFFFF)
    clean_config.add_color_to_history(0x123456)

    assert clean_config.fov_x == 400
    assert clean_config.target_color == 0xFFFFFF
    assert len(clean_config.color_history) > 0

    # Perform reset
    clean_config.reset_to_defaults()

    # Verify defaults restored
    assert clean_config.fov_x == 50  # Default from schema
    assert clean_config.target_color == 0xC9008D  # Default from schema
    assert clean_config.color_history == []


def test_reset_section_motion(clean_config):
    """Test granular reset for motion settings."""
    # Modify motion and vision settings
    clean_config.update("motion_min_cutoff", 10.0)
    clean_config.update("fov_x", 100)

    # Reset only motion
    clean_config.reset_motion_settings()

    # Verify motion reset but vision untouched
    assert clean_config.motion_min_cutoff == 0.5  # Default
    assert clean_config.fov_x == 100  # Modified value retained


def test_reset_section_vision(clean_config):
    """Test granular reset for vision settings."""
    # Modify motion and vision settings
    clean_config.update("motion_min_cutoff", 10.0)
    clean_config.update("fov_x", 100)

    # Reset only vision
    clean_config.reset_vision_settings()

    # Verify vision reset but motion untouched
    assert clean_config.motion_min_cutoff == 10.0  # Modified value retained
    assert clean_config.fov_x == 50  # Default


def test_create_backup(clean_config):
    """Test config backup creation."""
    # Ensure config file exists
    clean_config.save()
    original_path = clean_config.config_file

    # Create backup
    backup_path = clean_config.create_backup()

    assert backup_path != ""
    assert os.path.exists(backup_path)
    assert backup_path.startswith(original_path)
    assert backup_path.endswith(".bak")

    # Verify content matches
    with open(original_path) as f1, open(backup_path) as f2:
        assert json.load(f1) == json.load(f2)


def test_create_backup_failure_handling(clean_config):
    """Test backup failure handling (e.g., read-only filesystem simulation)."""
    # Mock shutil.copy2 to raise an exception
    with patch("shutil.copy2", side_effect=OSError("Disk full")):
        backup_path = clean_config.create_backup()
        assert backup_path == ""
