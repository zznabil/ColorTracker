#!/usr/bin/env python3

"""
Low-Level Movement System Module

Handles mouse movement using Windows API calls for game compatibility.
This implementation uses SendInput which is more likely to work in games
than high-level libraries like pyautogui or pynput.
"""

import ctypes
import time
from typing import Any


# Check for Windows environment or mocked environment
# We check if windll is available in ctypes (it might be mocked by conftest.py)
def is_windows_or_mocked() -> bool:
    return hasattr(ctypes, "windll")

# Windows API constants for mouse input (defined globally)
HC_ACTION = 0
WM_MOUSEMOVE = 0x0200
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
INPUT_MOUSE = 0

if is_windows_or_mocked():
    try:
        from ctypes import windll, wintypes
    except ImportError:
        # Should not happen if hasattr check passed, but safe guard
        windll = None
        wintypes = None

    # Define Windows API structures
    class POINT(ctypes.Structure):  # pyright: ignore[reportRedeclaration]
        """Windows POINT structure for coordinates"""

        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    class MOUSEINPUT(ctypes.Structure):  # pyright: ignore[reportRedeclaration]
        """Windows MOUSEINPUT structure for mouse events"""

        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
        ]

    class INPUT(ctypes.Structure):  # pyright: ignore[reportRedeclaration]
        """Windows INPUT structure for input events"""

        class _INPUT(ctypes.Union):
            _fields_ = [("mi", MOUSEINPUT)]

        _fields_ = [("type", wintypes.DWORD), ("ii", _INPUT)]

else:
    # Dummy definitions for non-Windows platforms to allow import
    windll: Any = None
    wintypes: Any = None

    class POINT:  # type: ignore
        def __init__(self, *args, **kwargs): pass
        x = 0
        y = 0

    class MOUSEINPUT:  # type: ignore
        def __init__(self, *args, **kwargs): pass

    class INPUT:  # type: ignore
        class _INPUT:
            def __init__(self, *args, **kwargs): pass
        def __init__(self, *args, **kwargs): pass


class LowLevelMovementSystem:
    """Handles low-level mouse movement using Windows API for game compatibility"""

    def __init__(self, config: Any) -> None:
        """
        Initialize the low-level movement system

        Args:
            config: Configuration object with movement settings
        """
        self.config = config

        # Movement settings
        # Dynamic access to config is used instead of caching
        # self.smoothing and self.aim_point are accessed from self.config directly

        # Ultra-responsive mode settings
        self.ultra_responsive_mode = getattr(config, "ultra_responsive_mode", False)
        self.zero_latency_mode = getattr(config, "zero_latency_mode", False)

        if is_windows_or_mocked() and windll is not None:
            # Get screen dimensions for absolute positioning
            # Check if GetSystemMetrics is mocked or real
            if hasattr(windll.user32, "GetSystemMetrics"):
                self.screen_width = windll.user32.GetSystemMetrics(0)
                self.screen_height = windll.user32.GetSystemMetrics(1)
            else:
                self.screen_width = 1920
                self.screen_height = 1080
        else:
            self.screen_width = 1920
            self.screen_height = 1080

        # Aim offset based on aim point
        self.aim_offset_y = 0

    def get_cursor_position(self) -> tuple[int, int]:
        """
        Get current cursor position using Windows API

        Returns:
            Tuple of (x, y) coordinates
        """
        if not is_windows_or_mocked() or windll is None:
            return 0, 0

        point = POINT()
        windll.user32.GetCursorPos(ctypes.byref(point))  # pyright: ignore[reportArgumentType]
        return point.x, point.y

    def move_mouse_relative(self, dx: int, dy: int) -> bool:
        """
        Move mouse by relative offset using SendInput (low-level)
        """
        if not is_windows_or_mocked() or windll is None:
            return True

        mouse_input = MOUSEINPUT(
            dx=dx, dy=dy, mouseData=0, dwFlags=MOUSEEVENTF_MOVE, time=0, dwExtraInfo=None
        )

        input_struct = INPUT(type=INPUT_MOUSE, ii=INPUT._INPUT(mi=mouse_input))

        # Send the input using Windows API with safety check
        try:
            result = windll.user32.SendInput(
                1,
                ctypes.byref(input_struct),  # pyright: ignore[reportArgumentType]
                ctypes.sizeof(INPUT),  # pyright: ignore[reportArgumentType]
            )
            return result == 1
        except Exception:
            return False

    def move_mouse_absolute(self, x: int, y: int) -> bool:
        """
        Move mouse to absolute position using SendInput (low-level)
        """
        if not is_windows_or_mocked() or windll is None:
            return True

        normalized_x = max(0, min(65535, int((x * 65535) / self.screen_width)))
        normalized_y = max(0, min(65535, int((y * 65535) / self.screen_height)))

        mouse_input = MOUSEINPUT(
            dx=normalized_x,
            dy=normalized_y,
            mouseData=0,
            dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
            time=0,
            dwExtraInfo=None,
        )

        input_struct = INPUT(type=INPUT_MOUSE, ii=INPUT._INPUT(mi=mouse_input))

        # Send the input using Windows API with safety check
        try:
            result = windll.user32.SendInput(
                1,
                ctypes.byref(input_struct),  # pyright: ignore[reportArgumentType]
                ctypes.sizeof(INPUT),  # pyright: ignore[reportArgumentType]
            )
            return result == 1
        except Exception:
            return False

    def move_to_target(self, target_x: int, target_y: int) -> None:
        """
        Move the mouse to center the target on the crosshair (screen center)
        """
        adjusted_target_y: int = self._apply_aim_offset(target_y)

        screen_center_x: int = self.screen_width // 2
        screen_center_y: int = self.screen_height // 2

        distance_x: int = target_x - screen_center_x
        distance_y: int = adjusted_target_y - screen_center_y

        move_x: int = distance_x
        move_y: int = distance_y

        if move_x != 0 or move_y != 0:
            success = self.move_mouse_relative(move_x, move_y)
            if not success:
                current_x, current_y = self.get_cursor_position()
                self.move_mouse_absolute(current_x + move_x, current_y + move_y)

    def _apply_aim_offset(self, target_y: int) -> int:
        """
        Apply vertical offset based on aim point setting
        """
        aim_point: int = getattr(self.config, "aim_point", 1)

        if aim_point == 0:
            return target_y - int(getattr(self.config, "head_offset", 10))
        elif aim_point == 1:
            return target_y
        elif aim_point == 2:
            return target_y + int(getattr(self.config, "leg_offset", 20))
        else:
            return target_y

    def aim_at(self, target_x: int, target_y: int) -> None:
        """
        Aim at the specified target coordinates
        """
        self.move_to_target(target_x, target_y)

    def test_movement(self) -> None:
        """
        Test the low-level movement system by moving the cursor in a small pattern
        This can be used to verify that the Windows API calls are working
        """
        print("Testing low-level mouse movement...")

        # Get starting position
        start_x, start_y = self.get_cursor_position()
        print(f"Starting position: ({start_x}, {start_y})")

        # Test relative movements
        print("Testing relative movements...")
        self.move_mouse_relative(50, 0)  # Move right
        time.sleep(0.1)
        self.move_mouse_relative(0, 50)  # Move down
        time.sleep(0.1)
        self.move_mouse_relative(-50, 0)  # Move left
        time.sleep(0.1)
        self.move_mouse_relative(0, -50)  # Move up
        time.sleep(0.1)

        # Return to starting position using absolute movement
        print("Returning to starting position...")
        self.move_mouse_absolute(start_x, start_y)

        final_x, final_y = self.get_cursor_position()
        print(f"Final position: ({final_x}, {final_y})")
        print("Low-level movement test completed!")
