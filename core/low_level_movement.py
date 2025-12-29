#!/usr/bin/env python3

"""
Low-Level Movement System Module

Handles mouse movement using Windows API calls for game compatibility.
This implementation uses SendInput which is more likely to work in games
than high-level libraries like pyautogui or pynput.

OPTIMIZATIONS (V3.4.0 ULTRATHINK):
- Cached User32 interface to eliminate repetitive attribute lookups.
- Protocol-based typing for safe interaction with ctypes.
- Zero-allocation structure reuse via Cached INPUT/MOUSEINPUT objects.
"""

import ctypes
import sys
import time
from typing import Any, Protocol, cast

# Conditionally import Windows-specific libraries or mock them
if sys.platform == "win32":
    try:
        from ctypes import windll, wintypes
    except ImportError:
        windll = None  # type: ignore
        wintypes = None  # type: ignore
else:
    # Mock classes/modules for non-Windows environments (e.g., Linux CI/CD)
    class MockWindll:
        class User32:
            def GetSystemMetrics(self, index):
                return 1920 if index == 0 else 1080

            def GetCursorPos(self, point_ref):
                # Correctly handle Pointer to POINT structures
                if hasattr(point_ref, "contents"):
                    point_ref.contents.x = 960
                    point_ref.contents.y = 540
                return 1

            def SendInput(self, nInputs, pInputs, cbSize):
                return 1

        user32 = User32()

    windll = MockWindll()  # type: ignore

    class MockWintypes:
        LONG = ctypes.c_long
        DWORD = ctypes.c_ulong
        ULONG = ctypes.c_ulong

    wintypes = MockWintypes()  # type: ignore


# Check for Windows environment or mocked environment
def is_windows_or_mocked() -> bool:
    """Check if we are on Windows or in a mocked environment suitable for movement logic"""
    return sys.platform == "win32" or hasattr(windll, "user32")


# Windows API constants for mouse input
HC_ACTION = 0
WM_MOUSEMOVE = 0x0200
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
INPUT_MOUSE = 0


# Define Windows API structures
class POINT(ctypes.Structure):
    """Windows POINT structure for coordinates"""

    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MOUSEINPUT(ctypes.Structure):
    """Windows MOUSEINPUT structure for mouse events"""

    _fields_ = [
        ("dx", wintypes.LONG),  # type: ignore
        ("dy", wintypes.LONG),  # type: ignore
        ("mouseData", wintypes.DWORD),  # type: ignore
        ("dwFlags", wintypes.DWORD),  # type: ignore
        ("time", wintypes.DWORD),  # type: ignore
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),  # type: ignore
    ]


class INPUT(ctypes.Structure):
    """Windows INPUT structure for input events"""

    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]

    _fields_ = [("type", wintypes.DWORD), ("ii", _INPUT)]  # type: ignore


# ULTRATHINK: Define Protocol for User32 to ensure type safety and allow mocking
class User32Protocol(Protocol):
    def GetSystemMetrics(self, nIndex: int) -> int: ...
    def GetCursorPos(self, lpPoint: Any) -> int: ...
    def SendInput(self, nInputs: int, pInputs: Any, cbSize: int) -> int: ...


class LowLevelMovementSystem:
    """
    [Archetype A: The Sage - Logic/Precision]
    Handles low-level mouse movement using Windows API (SendInput) with
    pre-allocated structure reuse for zero-allocation interaction.
    """

    def __init__(self, config: Any) -> None:
        """
        Initialize the low-level movement system

        Args:
            config: Configuration object with movement settings
        """
        self.config = config

        # Movement settings
        self.ultra_responsive_mode = getattr(config, "ultra_responsive_mode", False)
        self.zero_latency_mode = getattr(config, "zero_latency_mode", False)

        # Cache User32 interface
        self._user32: User32Protocol | None = self._resolve_user32()

        # Get screen dimensions for absolute positioning
        self.screen_width = 1920
        self.screen_height = 1080

        # Try to get actual metrics using cached user32
        if self._user32:
            try:
                self.screen_width = self._user32.GetSystemMetrics(0)
                self.screen_height = self._user32.GetSystemMetrics(1)
            except Exception:
                pass

        # Aim offset based on aim point
        self.aim_offset_y = 0

        # Optimization: Cache INPUT structure to avoid reallocation
        self._mouse_input = MOUSEINPUT()
        self._input_structure = INPUT(type=INPUT_MOUSE, ii=INPUT._INPUT(mi=self._mouse_input))

    def _resolve_user32(self) -> User32Protocol | None:
        """
        Resolves the user32 interface once at initialization.
        """
        # 1. Real Windows environment
        if hasattr(ctypes, "windll") and hasattr(ctypes.windll, "user32"):
            return cast(User32Protocol, ctypes.windll.user32)

        # 2. Mocked/Linux environment (fallback)
        if windll is not None and hasattr(windll, "user32"):
            return cast(User32Protocol, windll.user32)

        return None

    # Helper method for compatibility if tests rely on it, but internal code uses self._user32
    def _get_user32(self) -> User32Protocol | None:
        return self._user32

    def get_cursor_position(self) -> tuple[int, int]:
        """
        Get current cursor position using Windows API

        Returns:
            Tuple of (x, y) coordinates
        """
        if not self._user32:
            return 0, 0

        point = POINT()
        try:
            self._user32.GetCursorPos(ctypes.byref(point))
        except Exception:
            pass
        return point.x, point.y

    def move_mouse_relative(self, dx: int, dy: int) -> bool:
        """
        Move mouse by relative offset using SendInput (low-level)
        """
        if not self._user32:
            return True

        # Optimization: Reuse cached structure by updating fields directly
        # Note: We must update the structure inside the union, not a separate MOUSEINPUT object
        self._input_structure.ii.mi.dx = dx
        self._input_structure.ii.mi.dy = dy
        self._input_structure.ii.mi.mouseData = 0
        self._input_structure.ii.mi.dwFlags = MOUSEEVENTF_MOVE
        self._input_structure.ii.mi.time = 0
        self._input_structure.ii.mi.dwExtraInfo = None

        # Send the input using Windows API with safety check
        try:
            result = self._user32.SendInput(
                1, ctypes.byref(self._input_structure), ctypes.sizeof(INPUT)
            )
            return result == 1
        except Exception:
            return False

    def move_mouse_absolute(self, x: int, y: int) -> bool:
        """
        Move mouse to absolute position using SendInput (low-level)
        Using round() for better precision and (width-1) for correct mapping.
        """
        if not self._user32:
            return True

        # Normalize coordinates to 0-65535 range
        # We subtract 1 from screen dimensions because pixel coordinates are 0-indexed
        # e.g. x=1919 should map to 65535 on a 1920-wide screen
        normalized_x = max(0, min(65535, int(round((x * 65535) / (self.screen_width - 1)))))
        normalized_y = max(0, min(65535, int(round((y * 65535) / (self.screen_height - 1)))))

        # Optimization: Reuse cached structure by updating fields directly
        self._input_structure.ii.mi.dx = normalized_x
        self._input_structure.ii.mi.dy = normalized_y
        self._input_structure.ii.mi.mouseData = 0
        self._input_structure.ii.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
        self._input_structure.ii.mi.time = 0
        self._input_structure.ii.mi.dwExtraInfo = None

        # Send the input using Windows API with safety check
        try:
            result = self._user32.SendInput(
                1, ctypes.byref(self._input_structure), ctypes.sizeof(INPUT)
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
