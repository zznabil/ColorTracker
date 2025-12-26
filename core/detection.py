#!/usr/bin/env python3

"""
Detection System Module

Handles pixel search for target detection based on color.
"""

import threading

import cv2
import mss
import numpy as np


class DetectionSystem:
    """Handles pixel search for target detection based on color"""

    def __init__(self, config):
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

        # Search area optimization
        # self.search_area is accessed directly from config for real-time updates

    def _get_sct(self):
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
            img = np.array(sct.grab(local_area))
            if img is None or img.size == 0 or img.ndim != 3 or img.shape[2] != 4:
                return False, 0, 0
        except Exception:
            return False, 0, 0

        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        target_color = self._hex_to_bgr(self.config.target_color)

        if self.config.color_tolerance == 0:
            lower_bound = np.array(target_color, dtype=np.uint8)
            upper_bound = np.array(target_color, dtype=np.uint8)
        else:
            brightness_factor = self.config.color_tolerance * 2.5
            lower_bound = np.array([max(0, c - brightness_factor) for c in target_color], dtype=np.uint8)
            upper_bound = np.array([min(255, c + brightness_factor) for c in target_color], dtype=np.uint8)

        mask = cv2.inRange(img, lower_bound, upper_bound)
        matches = cv2.findNonZero(mask)

        if matches is not None and len(matches) > 0:
            match_x, match_y = matches[0][0]
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
            img = np.array(sct.grab(full_area))
            if img is None or img.size == 0 or img.ndim != 3 or img.shape[2] != 4:
                return False, 0, 0
        except Exception:
            # Handle screen capture errors gracefully
            # This prevents the TypeError: 160000 and similar buffer errors
            return False, 0, 0

        # Convert RGB to BGR (OpenCV format)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # Convert target color from hex to BGR
        target_color = self._hex_to_bgr(self.config.target_color)

        # Apply brightness/lightness tolerance to target color
        # Tolerance 0 means exact color, higher tolerance allows brighter/lighter variations
        if self.config.color_tolerance == 0:
            # Exact color match - use the target color directly
            lower_bound = np.array(target_color, dtype=np.uint8)
            upper_bound = np.array(target_color, dtype=np.uint8)
        else:
            # Calculate brightness variation based on tolerance
            # Higher tolerance = more brightness variation allowed
            brightness_factor = self.config.color_tolerance * 2.5  # Scale factor for noticeable effect

            # Calculate darker and lighter bounds
            darker_bound = np.array([max(0, c - brightness_factor) for c in target_color], dtype=np.uint8)
            lighter_bound = np.array([min(255, c + brightness_factor) for c in target_color], dtype=np.uint8)

            lower_bound = darker_bound
            upper_bound = lighter_bound

        # Create mask of pixels within color range
        mask = cv2.inRange(img, lower_bound, upper_bound)

        # Find coordinates of matching pixels
        matches = cv2.findNonZero(mask)

        if matches is not None and len(matches) > 0:
            # Get the first match (could implement more sophisticated selection)
            match_x, match_y = matches[0][0]

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
