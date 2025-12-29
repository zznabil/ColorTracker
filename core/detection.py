#!/usr/bin/env python3

"""
Detection System Module

Handles high-precision pixel search for target detection based on color.
OPTIMIZATIONS (V3.3.0 ULTRATHINK):
- Uses `cv2.minMaxLoc` for O(1) memory allocation during peak search.
- Zero-copy buffer architecture via `np.frombuffer` for ultra-low latency.
- Thread-local MSS instances for concurrent screen capture safety.
- Version-based Cache Invalidation (Observer Pattern) for O(1) config checks.
- Local Variable Caching in hot loops to eliminate attribute lookup overhead.
"""

import threading
from typing import Any

import cv2
import mss
import numpy as np
from numpy.typing import NDArray


class DetectionSystem:
    """
    [Archetype A: The Sage - Logic/Data]
    High-performance color detection system utilizing optimized screen capture
    and zero-copy buffer processing for ultra-low latency tracking.
    """

    # Type hints for cached values
    _lower_bound: NDArray[np.uint8] | None
    _upper_bound: NDArray[np.uint8] | None
    _last_target_color: int | None
    _last_color_tolerance: int | None

    def __init__(self, config: Any, perf_monitor: Any) -> None:
        """
        Initialize the detection system

        Args:
            config: Configuration object with detection settings
            perf_monitor: PerformanceMonitor instance for telemetry
        """
        self.config = config
        self.perf_monitor = perf_monitor

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

        # Caching for FOV calculations to avoid redundant arithmetic (GEM: From Session 9278)
        self._center_x = 0
        self._center_y = 0
        self._fov_x = 0
        self._fov_y = 0
        self._scan_area = None
        self._last_fov_config = None

        # ULTRATHINK: Version-based cache validation
        self._last_config_version = -1

        # Optimization: Pre-allocate capture area dictionaries to avoid per-frame allocation
        self._capture_area = {"left": 0, "top": 0, "width": 0, "height": 0}

    def _get_sct(self) -> Any:
        """
        Get thread-local MSS instance
        Creates a new MSS instance for each thread to prevent threading conflicts

        Returns:
            MSS instance for current thread
        """
        if not hasattr(self._local, "sct"):
            # Create new MSS instance for this thread
            # Optimization: Disable cursor capture for better performance
            self._local.sct = mss.mss(with_cursor=False)
        return self._local.sct

    def _update_color_bounds(self) -> None:
        """
        Updates the cached color bounds.
        Triggered only when config version changes.
        """
        current_color: int = self.config.target_color
        current_tolerance: int = self.config.color_tolerance

        target_bgr = self._hex_to_bgr(current_color)

        # Convert to 4-channel BGRA bounds (B, G, R, A)
        # The gain factor (2.5) results in a max reach of 250 at 100 tolerance.
        gain = 2.5
        lower_bgr = [max(0, int(c - current_tolerance * gain)) for c in target_bgr]
        upper_bgr = [min(255, int(c + current_tolerance * gain)) for c in target_bgr]

        self._lower_bound = np.array([lower_bgr[0], lower_bgr[1], lower_bgr[2], 0], dtype=np.uint8)
        self._upper_bound = np.array([upper_bgr[0], upper_bgr[1], upper_bgr[2], 255], dtype=np.uint8)

        # Cache update complete


    def _update_fov_cache(self) -> None:
        """
        Updates cached FOV and screen dimension values.
        Triggered only when config version changes.
        """
        # Cache dimensions locally to avoid config lookups in hot path
        self._screen_width = self.config.screen_width
        self._screen_height = self.config.screen_height

        w, h = self._screen_width, self._screen_height
        fov_x = self.config.fov_x
        fov_y = self.config.fov_y

        self._center_x = w // 2
        self._center_y = h // 2
        self._fov_x = fov_x
        self._fov_y = fov_y

        # Calculate FOV boundaries for full search
        scan_left = max(0, self._center_x - fov_x)
        scan_top = max(0, self._center_y - fov_y)
        scan_right = min(w, self._center_x + fov_x)
        scan_bottom = min(h, self._center_y + fov_y)

        self._scan_area = (scan_left, scan_top, scan_right, scan_bottom)
        # _last_fov_config removed as we use versioning now

    def find_target(self) -> tuple[bool, int, int]:
        """
        Search for target pixel color on screen
        """
        # ULTRATHINK: O(1) Version Check
        # Use getattr to support mocked config in tests which might not have _version
        current_version = getattr(self.config, "_version", 0)

        # Initialize if first run or config changed
        if current_version != self._last_config_version or self._scan_area is None:
            self._update_fov_cache()
            self._update_color_bounds()
            self._last_config_version = current_version

        # First try local search if we found a target in the previous frame
        if self.target_found_last_frame:
            result = self._local_search()
            if result[0]:
                return result

        # If local search failed or no previous target, do full FOV search
        # Using cached scan area
        if self._scan_area is None:
            return False, 0, 0

        scan_left, scan_top, scan_right, scan_bottom = self._scan_area
        return self._full_search(scan_left, scan_top, scan_right, scan_bottom)

    def _capture_and_process_frame(self, area: dict) -> tuple[bool, Any]:
        """
        Capture a frame from the screen and convert it to a NumPy array.

        Args:
            area: Dictionary with 'left', 'top', 'width', 'height' keys.

        Returns:
            Tuple of (success, image_data)
        """
        self.perf_monitor.start_probe("detection_capture")
        try:
            sct = self._get_sct()
            sct_img = sct.grab(area)
            # Use frombuffer to avoid memory copy
            img_bgra = np.frombuffer(sct_img.bgra, dtype=np.uint8).reshape((sct_img.height, sct_img.width, 4))

            if img_bgra.size == 0 or img_bgra.ndim != 3 or img_bgra.shape[2] != 4:
                return False, None

            return True, img_bgra
        except Exception:
            return False, None
        finally:
            self.perf_monitor.stop_probe("detection_capture")

    def _local_search(self) -> tuple[bool, int, int]:
        """
        Perform a local search around the last known target position.
        """
        # Calculate local search area with bounds checking
        # Calculate local search area with bounds checking
        # Hardcoded optimization margin (user feedback: slider removed)
        search_area: int = 100
        local_left = max(0, self.target_x - search_area)
        local_top = max(0, self.target_y - search_area)
        # Use cached screen dimensions
        local_right = min(self._screen_width, self.target_x + search_area)
        local_bottom = min(self._screen_height, self.target_y + search_area)

        # Calculate dimensions and validate
        width = local_right - local_left
        height = local_bottom - local_top

        if width <= 0 or height <= 0:
            return False, 0, 0

        # Optimization: Guard against excessively large search areas
        if width > 1000 or height > 1000:
            local_left, local_right, local_top, local_bottom = self._clamp_search_area(
                local_left, local_right, local_top, local_bottom, max_size=500
            )
            width, height = local_right - local_left, local_bottom - local_top

        # Optimization: Update pre-allocated dict instead of creating new one
        area = self._capture_area
        area["left"] = local_left
        area["top"] = local_top
        area["width"] = width
        area["height"] = height

        success, img_bgra = self._capture_and_process_frame(area)
        if not success:
            return False, 0, 0

        # Use cached bounds
        if self._lower_bound is None or self._upper_bound is None:
            self._update_color_bounds()

        self.perf_monitor.start_probe("detection_process")
        try:
            mask = cv2.inRange(img_bgra, self._lower_bound, self._upper_bound)  # type: ignore
            _, max_val, _, max_loc = cv2.minMaxLoc(mask)
        finally:
            self.perf_monitor.stop_probe("detection_process")

        if max_val <= 0:
            return False, 0, 0

        screen_x, screen_y = int(max_loc[0] + local_left), int(max_loc[1] + local_top)

        # FOV Restriction Check
        # Use cached values to avoid redundant calculations and attribute access
        if abs(screen_x - self._center_x) > self._fov_x or abs(screen_y - self._center_y) > self._fov_y:
            self.target_found_last_frame = False
            return False, 0, 0

        self.target_x, self.target_y = screen_x, screen_y
        self.target_found_last_frame = True
        return True, screen_x, screen_y

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

        # Optimization: Clamp very large search areas
        left, right, top, bottom = self._clamp_search_area(left, right, top, bottom, max_size=1500)
        width = right - left
        height = bottom - top

        # Optimization: Update pre-allocated dict
        area = self._capture_area
        area["left"] = left
        area["top"] = top
        area["width"] = width
        area["height"] = height

        success, img_bgra = self._capture_and_process_frame(area)
        if not success:
            return False, 0, 0

        # OPTIMIZATION: Removed cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2BGR)
        # We now perform color matching directly on BGRA data.

        # Use cached bounds
        if self._lower_bound is None or self._upper_bound is None:
            self._update_color_bounds()

        self.perf_monitor.start_probe("detection_process")
        try:
            # Create mask of pixels within color range
            mask = cv2.inRange(img_bgra, self._lower_bound, self._upper_bound)  # type: ignore

            # OPTIMIZATION: Use minMaxLoc instead of findNonZero
            _, max_val, _, max_loc = cv2.minMaxLoc(mask)
        finally:
            self.perf_monitor.stop_probe("detection_process")

        if max_val <= 0:
            # No match found in full search
            self.target_found_last_frame = False
            return False, 0, 0

        match_x, match_y = max_loc

        # Convert back to screen coordinates
        screen_x = match_x + left
        screen_y = match_y + top

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
