#!/usr/bin/env python3

"""
Paths Utility

Provides robust path resolution for the application, handling both
standard script execution and frozen (PyInstaller) states.
"""

import os
import sys


def get_app_dir() -> str:
    """
    Get the application's root directory.

    Handles two cases:
    1. Frozen (PyInstaller): Returns the directory containing the executable.
    2. Script: Returns the project root directory (assuming this file is in utils/).

    Returns:
        str: The absolute path to the application root.
    """
    if getattr(sys, "frozen", False):
        # In frozen mode (PyInstaller), sys.executable is the path to the .exe
        return os.path.dirname(sys.executable)

    # In script mode, this file is in /utils/paths.py
    # So we go up two levels to get to the project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
