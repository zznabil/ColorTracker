#!/usr/bin/env python3

"""
Screen Information Utility

Provides information about the screen dimensions.
"""


import pyautogui


class ScreenInfo:
    """Provides information about the screen dimensions"""

    @staticmethod
    def get_screen_size() -> tuple[int, int]:
        """
        Get the screen width and height

        Returns:
            Tuple of (width, height)
        """
        return pyautogui.size()

    @staticmethod
    def get_screen_center() -> tuple[int, int]:
        """
        Get the coordinates of the screen center

        Returns:
            Tuple of (center_x, center_y)
        """
        width, height = pyautogui.size()
        return (width // 2, height // 2)
