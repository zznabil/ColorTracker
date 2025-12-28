import os
import sys
from unittest.mock import patch

from utils.paths import get_app_dir


def test_get_app_dir_script_mode():
    """Test get_app_dir when running as a script"""
    # Ensure frozen is False
    with patch.object(sys, "frozen", False, create=True):
        # detailed verification is tricky because __file__ depends on where pytest is run
        # but we can verify it returns a valid directory that contains 'utils'
        app_dir = get_app_dir()
        assert os.path.isdir(app_dir)
        # Check integrity relative to this test file
        # This test file is in tests/, paths.py is in utils/
        # get_app_dir should return the project root
        assert os.path.exists(os.path.join(app_dir, "utils", "paths.py"))


def test_get_app_dir_frozen_mode():
    """Test get_app_dir when running as a frozen executable"""
    mock_exe_path = os.path.abspath(r"C:\Path\To\Dist\MyApp.exe")
    expected_dir = os.path.dirname(mock_exe_path)

    with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", mock_exe_path):
        app_dir = get_app_dir()
        assert app_dir == expected_dir
