#!/usr/bin/env python3

"""
Detection System Module

Handles pixel search for target detection based on color.
Optimization: Uses cv2.minMaxLoc instead of cv2.findNonZero for O(1) memory allocation.
"""

import threading
from typing import Any

import cv2
import mss
import numpy as np
from numpy.typing import NDArray


class DetectionSystem:
    """Handles pixel search for target detection based on color"""

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
            # Alpha is set to 0-255 to match any alpha value
            if current_tolerance == 0:
                self._lower_bound = np.array([*target_bgr, 0], dtype=np.uint8)
                self._upper_bound = np.array([*target_bgr, 255], dtype=np.uint8)
            else:
                brightness_factor = current_tolerance * 2.5
                lower_bgr = [max(0, c - brightness_factor) for c in target_bgr]
                upper_bgr = [min(255, c + brightness_factor) for c in target_bgr]

                self._lower_bound = np.array([*lower_bgr, 0], dtype=np.uint8)
                self._upper_bound = np.array([*upper_bgr, 255], dtype=np.uint8)

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

    def _local_search(self) -> tuple[bool, int, int]:
        """
        Perform a local search around the last known target position
        """
        # Calculate local search area with bounds checking
        search_area: int = self.config.search_area
        local_left: int = max(0, self.target_x - search_area)
        local_top: int = max(0, self.target_y - search_area)
        local_right: int = min(self.config.screen_width, self.target_x + search_area)
        local_bottom: int = min(self.config.screen_height, self.target_y + search_area)

        # Calculate dimensions and validate them
        width: int = local_right - local_left
        height: int = local_bottom - local_top

        if width <= 0 or height <= 0:
            return False, 0, 0

        if width > 1000 or height > 1000:
            max_size = 500
            if width > max_size:
                excess = (width - max_size) // 2
                local_left += excess
                local_right -= excess
                width = local_right - local_left
            if height > max_size:
                excess = (height - max_size) // 2
                local_top += excess
                local_bottom -= excess
                height = local_bottom - local_top

        local_area = {"left": local_left, "top": local_top, "width": width, "height": height}

        try:
            sct = self._get_sct()
            img_bgra = np.array(sct.grab(local_area))
            if img_bgra is None or img_bgra.size == 0 or img_bgra.ndim != 3 or img_bgra.shape[2] != 4:
                return False, 0, 0
        except Exception:
            return False, 0, 0

        # OPTIMIZATION: Removed cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2BGR)
        # We now perform color matching directly on BGRA data.
        # This saves O(N) allocation and CPU cycles per frame.

        # Use cached bounds
        if self._lower_bound is None or self._upper_bound is None:
            self._update_color_bounds()

        mask = cv2.inRange(img_bgra, self._lower_bound, self._upper_bound)  # type: ignore

        # OPTIMIZATION: Use minMaxLoc instead of findNonZero
        # findNonZero allocates memory for ALL matching points (O(N))
        # minMaxLoc finds the max value (255 if match exists) and its location in O(1) memory
        _, max_val, _, max_loc = cv2.minMaxLoc(mask)

        if max_val > 0:
            match_x, match_y = max_loc
            screen_x: int = int(match_x + local_left)
            screen_y: int = int(match_y + local_top)

            # --- FOV Restriction Check ---
            # Ensure the target found in local search is still within the global FOV bounds
            center_x: int = self.config.screen_width // 2
            center_y: int = self.config.screen_height // 2

            if abs(screen_x - center_x) > self.config.fov_x or abs(screen_y - center_y) > self.config.fov_y:
                self.target_found_last_frame = False
                return False, 0, 0
            # -----------------------------

            self.target_x = screen_x
            self.target_y = screen_y
            self.target_found_last_frame = True
            return True, screen_x, screen_y

        return False, 0, 0

    def _full_search(self, left: int, top: int, right: int, bottom: int) -> tuple[bool, int, int]:
        """
        Perform a full search within the specified boundaries

        Args:
            left: Left boundary of search area
            top: Top boundary of search area
            right: Right boundary of search area
            bottom: Bottom boundary of search area

        Returns:
            Tuple containing target found status and coordinates
        """
        # Calculate dimensions and validate them
        width = right - left
        height = bottom - top

        # Validate area dimensions to prevent buffer overflow
        # MSS has issues with very large areas or invalid dimensions
        if width <= 0 or height <= 0:
            # Invalid dimensions - return no target found
            return False, 0, 0

        if width > 2000 or height > 2000:
            # Area too large - clamp to reasonable size
            max_size = 1500
            if width > max_size:
                excess = (width - max_size) // 2
                left += excess
                right -= excess
                width = right - left
            if height > max_size:
                excess = (height - max_size) // 2
                top += excess
                bottom -= excess
                height = bottom - top

        # Create capture area dictionary
        full_area = {"left": left, "top": top, "width": width, "height": height}

        try:
            # Use thread-local MSS instance to prevent threading conflicts
            sct = self._get_sct()
            img_bgra = np.array(sct.grab(full_area))
            if img_bgra is None or img_bgra.size == 0 or img_bgra.ndim != 3 or img_bgra.shape[2] != 4:
                return False, 0, 0
        except Exception:
            # Handle screen capture errors gracefully
            return False, 0, 0

        # OPTIMIZATION: Removed cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2BGR)
        # We now perform color matching directly on BGRA data.

        # Use cached bounds
        if self._lower_bound is None or self._upper_bound is None:
            self._update_color_bounds()

        # Create mask of pixels within color range
        mask = cv2.inRange(img_bgra, self._lower_bound, self._upper_bound)  # type: ignore

        # OPTIMIZATION: Use minMaxLoc instead of findNonZero
        _, max_val, _, max_loc = cv2.minMaxLoc(mask)

        if max_val > 0:
            match_x, match_y = max_loc

            # Convert back to screen coordinates
            screen_x = match_x + left
            screen_y = match_y + top

            # Update target position
            self.target_x = screen_x
            self.target_y = screen_y
            self.target_found_last_frame = True

            return True, screen_x, screen_y

        # No match found in full search
        self.target_found_last_frame = False
        return False, 0, 0

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
