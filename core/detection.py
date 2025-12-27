#!/usr/bin/env python3

"""
Detection System Module

Handles high-precision pixel search for target detection based on color.
OPTIMIZATIONS:
- Uses `cv2.minMaxLoc` for O(1) memory allocation during peak search.
- Zero-copy buffer architecture via `np.frombuffer` for ultra-low latency.
- Thread-local MSS instances for concurrent screen capture safety.
- Unified `_detect_in_area` hot path to eliminate method call overhead.
"""

import threading
from typing import Any

import cv2
import mss
import numpy as np
from numpy.typing import NDArray


class DetectionSystem:
    """
    High-performance color detection system utilizing optimized screen capture
    and zero-copy buffer processing for ultra-low latency tracking.
    """

    # Type hints for cached values
    _lower_bound: NDArray[np.uint8] | None
    _upper_bound: NDArray[np.uint8] | None
    _last_target_color: int | None
    _last_color_tolerance: int | None

    def __init__(self, config: Any) -> None:
        """
        Initialize the detection system

        Args:
            config: Configuration object with detection settings
        """
        self.config = config

        # Initialize thread-local storage for MSS instances
        # This prevents threading issues with screen capture
        self._local = threading.local()

        # Target position tracking
        self.target_x = 0
        self.target_y = 0
        self.target_found_last_frame = False

        # Caching for color bounds to avoid re-calculation per frame
        self._lower_bound = None
        self._upper_bound = None
        self._last_target_color = None
        self._last_color_tolerance = None

    def _get_sct(self) -> Any:
        """
        Get thread-local MSS instance
        Creates a new MSS instance for each thread to prevent threading conflicts

        Returns:
            MSS instance for current thread
        """
        if not hasattr(self._local, "sct"):
            # Create new MSS instance for this thread
            self._local.sct = mss.mss()
        return self._local.sct

    def _update_color_bounds(self) -> None:
        """
        Updates the cached color bounds if config has changed.
        This avoids re-calculating bounds and re-converting hex to BGR every frame.
        """
        current_color: int = self.config.target_color
        current_tolerance: int = self.config.color_tolerance

        if (
            self._lower_bound is None
            or current_color != self._last_target_color
            or current_tolerance != self._last_color_tolerance
        ):
            target_bgr = self._hex_to_bgr(current_color)

            # Convert to 4-channel BGRA bounds (B, G, R, A)
            if current_tolerance == 0:
                self._lower_bound = np.array([target_bgr[0], target_bgr[1], target_bgr[2], 0], dtype=np.uint8)
                self._upper_bound = np.array([target_bgr[0], target_bgr[1], target_bgr[2], 255], dtype=np.uint8)
            else:
                # The gain factor (2.5) results in a max reach of 250 at 100 tolerance.
                # This covers almost the entire 0-255 spectrum if needed.
                gain = 2.5
                lower_bgr = [max(0, int(c - current_tolerance * gain)) for c in target_bgr]
                upper_bgr = [min(255, int(c + current_tolerance * gain)) for c in target_bgr]

                self._lower_bound = np.array([lower_bgr[0], lower_bgr[1], lower_bgr[2], 0], dtype=np.uint8)
                self._upper_bound = np.array([upper_bgr[0], upper_bgr[1], upper_bgr[2], 255], dtype=np.uint8)

            self._last_target_color = current_color
            self._last_color_tolerance = current_tolerance

    def find_target(self) -> tuple[bool, int, int]:
        """
        Search for target pixel color on screen
        """
        # Get screen center coordinates
        center_x: int = self.config.screen_width // 2
        center_y: int = self.config.screen_height // 2

        # Calculate FOV boundaries
        scan_left: int = center_x - self.config.fov_x
        scan_top: int = center_y - self.config.fov_y
        scan_right: int = center_x + self.config.fov_x
        scan_bottom: int = center_y + self.config.fov_y

        # Ensure boundaries are within screen
        scan_left = max(0, scan_left)
        scan_top = max(0, scan_top)
        scan_right = min(self.config.screen_width, scan_right)
        scan_bottom = min(self.config.screen_height, scan_bottom)

        # Update color bounds cache
        self._update_color_bounds()

        # First try local search if we found a target in the previous frame
        if self.target_found_last_frame:
            result = self._local_search()
            if result[0]:
                return result

        # If local search failed or no previous target, do full FOV search
        return self._full_search(scan_left, scan_top, scan_right, scan_bottom)

    def _detect_in_area(self, left: int, top: int, width: int, height: int) -> tuple[bool, int, int]:
        """
        Unified high-performance detection logic.
        Combines clamping, capturing, masking, and locating to reduce method call overhead.
        This is the 'Hot Path' of the detection system.

        Args:
            left: Left coordinate
            top: Top coordinate
            width: Width of capture area
            height: Height of capture area

        Returns:
            Tuple (success, x, y) in screen coordinates
        """
        if width <= 0 or height <= 0:
            return False, 0, 0

        try:
            # Use method for testability (mocking support)
            sct = self._get_sct()

            # mss.grab requires strict int types and specific keys
            area = {"left": int(left), "top": int(top), "width": int(width), "height": int(height)}
            sct_img = sct.grab(area)

            # Zero-copy conversion
            img_bgra = np.frombuffer(sct_img.bgra, dtype=np.uint8).reshape((sct_img.height, sct_img.width, 4))
        except Exception:
            return False, 0, 0

        if img_bgra.size == 0:
            return False, 0, 0

        # Masking
        # Note: _lower_bound and _upper_bound are guaranteed to be set by find_target calling _update_color_bounds
        # But for safety we check.
        if self._lower_bound is None:
            self._update_color_bounds()

        mask = cv2.inRange(img_bgra, self._lower_bound, self._upper_bound) # type: ignore
        _, max_val, _, max_loc = cv2.minMaxLoc(mask)

        if max_val <= 0:
            return False, 0, 0

        # Return global coordinates
        return True, int(max_loc[0] + left), int(max_loc[1] + top)

    def _local_search(self) -> tuple[bool, int, int]:
        """
        Perform a local search around the last known target position.
        """
        # Calculate local search area with bounds checking
        search_area: int = self.config.search_area
        local_left = max(0, self.target_x - search_area)
        local_top = max(0, self.target_y - search_area)
        local_right = min(self.config.screen_width, self.target_x + search_area)
        local_bottom = min(self.config.screen_height, self.target_y + search_area)

        # Calculate dimensions
        width = local_right - local_left
        height = local_bottom - local_top

        # Optimization: Guard against excessively large search areas
        if width > 1000 or height > 1000:
            local_left, local_right, local_top, local_bottom = self._clamp_search_area(
                local_left, local_right, local_top, local_bottom, max_size=500
            )
            width, height = local_right - local_left, local_bottom - local_top

        # Perform detection
        success, screen_x, screen_y = self._detect_in_area(local_left, local_top, width, height)

        if not success:
            return False, 0, 0

        # FOV Restriction Check
        center_x, center_y = self.config.screen_width // 2, self.config.screen_height // 2
        if abs(screen_x - center_x) > self.config.fov_x or abs(screen_y - center_y) > self.config.fov_y:
            self.target_found_last_frame = False
            return False, 0, 0

        self.target_x, self.target_y = screen_x, screen_y
        self.target_found_last_frame = True
        return True, screen_x, screen_y

    def _full_search(self, left: int, top: int, right: int, bottom: int) -> tuple[bool, int, int]:
        """
        Perform a full search within the specified boundaries
        """
        # Calculate dimensions
        width = right - left
        height = bottom - top

        # Optimization: Clamp very large search areas
        left, right, top, bottom = self._clamp_search_area(left, right, top, bottom, max_size=1500)
        width = right - left
        height = bottom - top

        # Perform detection
        success, screen_x, screen_y = self._detect_in_area(left, top, width, height)

        if not success:
            self.target_found_last_frame = False
            return False, 0, 0

        # Update target position
        self.target_x = screen_x
        self.target_y = screen_y
        self.target_found_last_frame = True

        return True, screen_x, screen_y

    def _hex_to_bgr(self, hex_color: int) -> tuple[int, int, int]:
        """
        Convert hex color to BGR tuple

        Args:
            hex_color: Color in hexadecimal format (e.g., 0xc9008d)

        Returns:
            Tuple of (Blue, Green, Red) values
        """
        # Extract RGB components
        r = (hex_color >> 16) & 0xFF
        g = (hex_color >> 8) & 0xFF
        b = hex_color & 0xFF

        # Return as BGR (OpenCV format)
        return (b, g, r)

    def _clamp_search_area(
        self, left: int, right: int, top: int, bottom: int, max_size: int
    ) -> tuple[int, int, int, int]:
        """
        Clamps a search area symmetrically to a maximum size if it exceeds it.
        Helper for DRY consolidation.
        """
        width = right - left
        height = bottom - top

        # Only clamp if the area is significantly oversized
        if width > max_size:
            excess = (width - max_size) // 2
            left += excess
            right -= excess
        if height > max_size:
            excess = (height - max_size) // 2
            top += excess
            bottom -= excess

        return left, right, top, bottom
