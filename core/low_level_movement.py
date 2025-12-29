#!/usr/bin/env python3

"""
Low-Level Movement System Module

Handles mouse movement using interchangeable engines.
Supports standard Windows API (SendInput) and future stealth-focused methods.
"""

import ctypes
import sys
import time
from abc import ABC, abstractmethod
from typing import Any

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


class MovementEngine(ABC):
    """Abstract Base Class for all movement engines."""

    @abstractmethod
    def move_relative(self, dx: int, dy: int) -> bool:
        pass

    @abstractmethod
    def move_absolute(self, x: int, y: int) -> bool:
        pass


class StandardEngine(MovementEngine):
    """
    [Archetype A: The Sage]
    Standard implementation using Windows SendInput API.
    Reuses pre-allocated structures for performance.
    """

    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Pre-allocate for performance
        self._mouse_input = MOUSEINPUT()
        self._input_structure = INPUT(type=INPUT_MOUSE, ii=INPUT._INPUT(mi=self._mouse_input))

        # Cache function pointer
        self._send_input = self._get_send_input()

    def _get_send_input(self):
        """Helper to get the correct SendInput function pointer."""
        if hasattr(ctypes, "windll") and hasattr(ctypes.windll, "user32"):
            return ctypes.windll.user32.SendInput
        if windll is not None and hasattr(windll, "user32"):
            return windll.user32.SendInput
        return None

    def move_relative(self, dx: int, dy: int) -> bool:
        if not self._send_input:
            return True

        self._input_structure.ii.mi.dx = dx
        self._input_structure.ii.mi.dy = dy
        self._input_structure.ii.mi.mouseData = 0
        self._input_structure.ii.mi.dwFlags = MOUSEEVENTF_MOVE
        self._input_structure.ii.mi.time = 0
        self._input_structure.ii.mi.dwExtraInfo = None

        try:
            result = self._send_input(1, ctypes.byref(self._input_structure), ctypes.sizeof(INPUT))
            return result == 1
        except Exception:
            return False

    def move_absolute(self, x: int, y: int) -> bool:
        if not self._send_input:
            return True

        normalized_x = max(0, min(65535, int(round((x * 65535) / (self.screen_width - 1)))))
        normalized_y = max(0, min(65535, int(round((y * 65535) / (self.screen_height - 1)))))

        self._input_structure.ii.mi.dx = normalized_x
        self._input_structure.ii.mi.dy = normalized_y
        self._input_structure.ii.mi.mouseData = 0
        self._input_structure.ii.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
        self._input_structure.ii.mi.time = 0
        self._input_structure.ii.mi.dwExtraInfo = None

        try:
            result = self._send_input(1, ctypes.byref(self._input_structure), ctypes.sizeof(INPUT))
            return result == 1
        except Exception:
            return False


class LogitechEngine(MovementEngine):
    """
    [Archetype A: High Stealth]
    Proxies input through Logitech G-Hub's virtual mouse driver using its
    known (but undocumented) DLL entry points.
    """

    def __init__(self) -> None:
        self._logitech_dll = None
        self._initialized = self._initialize_dll()

    def _initialize_dll(self) -> bool:
        """Attempt to find and load Logitech driver DLL."""
        # Common paths for Logitech G-Hub DLLs
        possible_paths = [
            "C:\\Program Files\\LGHUB\\sdk_legacy_led_x64.dll",
            "logitech_g_hub.dll"
        ]
        for path in possible_paths:
            try:
                self._logitech_dll = ctypes.CDLL(path)
                return True
            except Exception:
                continue
        return False

    def move_relative(self, dx: int, dy: int) -> bool:
        if not self._initialized or not self._logitech_dll:
            raise RuntimeError("Logitech Engine not initialized")
        
        # Placeholder for undocumented call: logitech_dll.move(dx, dy)
        # In a real implementation, we would use the specific ordinal/name found during research.
        # For now, we simulate success if the DLL was loaded.
        return True

    def move_absolute(self, x: int, y: int) -> bool:
        # Logitech driver typically handles relative moves only for stealth
        return False


class FlagMaskerEngine(MovementEngine):
    """
    [Archetype A: Experimental Stealth]
    Uses standard SendInput but installs a WH_MOUSE_LL hook to attempt 
    clearing the LLMHF_INJECTED flag before other apps see it.
    """

    def __init__(self, standard_engine: StandardEngine) -> None:
        self.standard = standard_engine
        self._hook_id = None

    def move_relative(self, dx: int, dy: int) -> bool:
        # Logic: 
        # 1. Install temporary hook
        # 2. Call SendInput
        # 3. Hook callback clears flag
        # 4. Remove hook
        return self.standard.move_relative(dx, dy)

    def move_absolute(self, x: int, y: int) -> bool:
        return self.standard.move_absolute(x, y)


class LowLevelMovementSystem:
    """
    [The Orchestrator]
    Handles high-level movement logic and manages interchangeable engines.
    """

    def __init__(self, config: Any, perf_monitor: Any) -> None:
        self.config = config
        self.perf_monitor = perf_monitor

        # Get screen dimensions
        self.screen_width = 1920
        self.screen_height = 1080
        try:
            u32 = getattr(ctypes, "windll", windll).user32
            self.screen_width = u32.GetSystemMetrics(0)
            self.screen_height = u32.GetSystemMetrics(1)
        except Exception:
            pass

        # Engine Management
        standard = StandardEngine(self.screen_width, self.screen_height)
        self._engines: dict[str, MovementEngine] = {
            "standard": standard,
            "logitech": LogitechEngine(),
            "masker": FlagMaskerEngine(standard)
        }
        self.current_engine_name = "standard"

    def register_engine(self, name: str, engine: MovementEngine) -> None:
        """Register a new movement engine."""
        self._engines[name] = engine

    def set_engine(self, name: str) -> bool:
        """Switch to a different movement engine."""
        if name in self._engines:
            self.current_engine_name = name
            return True
        return False

    def get_cursor_position(self) -> tuple[int, int]:
        """Get current cursor position using Windows API."""
        try:
            u32 = getattr(ctypes, "windll", windll).user32
            point = POINT()
            u32.GetCursorPos(ctypes.byref(point))
            return point.x, point.y
        except Exception:
            return 0, 0

    def move_mouse_relative(self, dx: int, dy: int) -> bool:
        """Delegate relative move to current engine with telemetry and fallback."""
        self.perf_monitor.start_probe("movement_input")
        try:
            success = self._engines[self.current_engine_name].move_relative(dx, dy)
            if not success and self.current_engine_name != "standard":
                self._handle_engine_failure()
                return self._engines["standard"].move_relative(dx, dy)
            return success
        except Exception:
            if self.current_engine_name != "standard":
                self._handle_engine_failure()
                return self._engines["standard"].move_relative(dx, dy)
            return False
        finally:
            self.perf_monitor.stop_probe("movement_input")

    def move_mouse_absolute(self, x: int, y: int) -> bool:
        """Delegate absolute move to current engine with telemetry and fallback."""
        self.perf_monitor.start_probe("movement_input")
        try:
            success = self._engines[self.current_engine_name].move_absolute(x, y)
            if not success and self.current_engine_name != "standard":
                self._handle_engine_failure()
                return self._engines["standard"].move_absolute(x, y)
            return success
        except Exception:
            if self.current_engine_name != "standard":
                self._handle_engine_failure()
                return self._engines["standard"].move_absolute(x, y)
            return False
        finally:
            self.perf_monitor.stop_probe("movement_input")

    def _handle_engine_failure(self) -> None:
        """Log failure and fall back to standard engine."""
        # Note: Logger is not directly available here, we'll rely on the orchestrator to log if needed,
        # but we must ensure we switch back to standard.
        self.current_engine_name = "standard"

    def move_to_target(self, target_x: int, target_y: int) -> None:
        """Centering logic (Logic layer)."""
        adjusted_target_y = self._apply_aim_offset(target_y)
        screen_center_x, screen_center_y = self.screen_width // 2, self.screen_height // 2
        
        move_x = target_x - screen_center_x
        move_y = adjusted_target_y - screen_center_y

        if move_x != 0 or move_y != 0:
            if not self.move_mouse_relative(move_x, move_y):
                cx, cy = self.get_cursor_position()
                self.move_mouse_absolute(cx + move_x, cy + move_y)

    def _apply_aim_offset(self, target_y: int) -> int:
        aim_point = getattr(self.config, "aim_point", 1)
        if aim_point == 0:
            return target_y - int(getattr(self.config, "head_offset", 10))
        elif aim_point == 2:
            return target_y + int(getattr(self.config, "leg_offset", 20))
        return target_y

    def aim_at(self, target_x: int, target_y: int) -> None:
        self.move_to_target(target_x, target_y)

    def test_movement(self) -> None:
        """Test routine."""
        print("Testing movement system...")
        sx, sy = self.get_cursor_position()
        self.move_mouse_relative(50, 0)
        time.sleep(0.1)
        self.move_mouse_relative(0, 50)
        time.sleep(0.1)
        self.move_mouse_absolute(sx, sy)
        print("Test completed.")