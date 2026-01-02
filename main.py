#!/usr/bin/env python3

"""
Color Tracking Algo for Single Player Games in Development - V3.4.1

Main entry point for the Color Tracking Algo application, orchestrated
for high-performance detection and responsive UI.
"""

import ctypes
import logging
import sys
import threading
import time
from typing import Any

import dearpygui.dearpygui as dpg
import mss
import numpy as np

from core.detection import DetectionSystem
from core.low_level_movement import LowLevelMovementSystem
from core.motion_engine import MotionEngine
from gui.main_window import setup_gui
from utils.config import Config
from utils.keyboard_listener import KeyboardListener
from utils.logger import Logger
from utils.performance_monitor import PerformanceMonitor
from utils.screen_info import ScreenInfo

# Make the application DPI aware to fix coordinate scaling issues on high-DPI monitors
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


class ColorTrackerAlgo:
    """
    [The Orchestrator]
    Main application class for Color Tracking Algo with optimized performance and responsiveness.
    """

    # Explicitly declare dynamic attributes for static analysis (Pyright)
    status_text: int | str
    fps_text: int | str
    enabled_checkbox: int | str
    update_target_status: Any
    update_analytics: Any
    refresh_ui_from_config: Any
    start_time: float

    def __init__(self):
        # State Initialization
        self.running = False
        self.thread = None
        self.fps = 0.0
        self.frame_count = 0
        self._target_status_cache = None

        # 1. Initialize DearPyGUI context first
        dpg.create_context()

        # 2. Create logger with optimized settings and startup safety
        try:
            self.logger = Logger(log_level=logging.DEBUG, log_to_file=True)
            self.logger.install_global_exception_handler()  # Catch unhandled exceptions
            self.logger.info("ColorTracker Algorithm V3 starting...")
            self.logger.debug("Debug logging enabled - all operations will be logged verbosely")
            self.logger.info("Debug console enabled - Press F12 to toggle debug console")
        except Exception as e:
            print(f"CRITICAL: Failed to initialize Logger. {e}")

            # Fallback mock logger if file permission fails
            class MockLogger:
                def info(self, m):
                    print(f"[INFO] {m}")

                def error(self, m):
                    print(f"[ERROR] {m}")

                def debug(self, m):
                    pass

                def warning(self, m):
                    print(f"[WARN] {m}")

                def critical(self, m):
                    print(f"[CRITICAL] {m}")

                @property
                def debug_console_enabled(self):
                    return False

                def toggle_debug_console(self):
                    return False

            self.logger = MockLogger()

        # 3. Load configuration
        self.config = Config()
        self.config.load()

        # 4. Get screen information and log system details
        screen_width, screen_height = ScreenInfo.get_screen_size()
        self.config.screen_width = screen_width
        self.config.screen_height = screen_height
        self.logger.debug(f"Screen resolution detected: {screen_width}x{screen_height}")

        # 5. Initialize performance monitor
        self.perf_monitor = PerformanceMonitor()

        # 6. Initialize systems with optimized settings
        self.logger.debug("Initializing detection system...")
        self.detection = DetectionSystem(self.config, self.perf_monitor)
        self.logger.debug("Initializing unified motion engine...")
        self.motion_engine = MotionEngine(self.config)

        # 7. Initialize movement system with optimized settings
        self.logger.debug("Initializing low-level movement system for game compatibility...")
        self.movement = LowLevelMovementSystem(self.config, self.perf_monitor)
        self.logger.debug("All core systems initialized successfully with low-level mouse input")

        # 8. Initialize keyboard listener with optimized settings
        self.keyboard = KeyboardListener(self.config)
        self.keyboard.start()  # Start the background listener thread
        self._mouse_listener = None  # For scroll-to-zoom in picking mode

        # 9. Magnifier State (The Precision Lens Redesign)
        self.picking_mode = False
        self._magnifier_window = None
        self._magnifier_texture = None
        self._magnifier_data = None
        self._magnifier_size = 160  # Slightly larger for better clarity
        self._zoom_levels = [8, 10, 16, 20]  # Optimized divisors for 160
        self._zoom_index = 1  # Default to 10 (index 1)
        self._zoom_level = self._zoom_levels[self._zoom_index]
        self._magnifier_scale = self._magnifier_size // self._zoom_level

        # 10. Viewport state for Global Magnifier
        self._viewport_original_width = 500
        self._viewport_original_height = 750
        self._viewport_original_pos = [100, 100]
        self._viewport_original_decorated = True
        self._viewport_original_always_on_top = False

        # 11. GUI Update interval
        self._ui_update_interval = 0.1
        self._last_ui_update = 0
        self._gui_cache = {}
        self._analytics_update_interval = 0.5
        self._last_analytics_update = 0

        # 12. Initialize GUI and viewport (MUST BE LAST)
        self.logger.debug("Setting up DearPyGUI interface...")
        try:
            setup_gui(self)
            dpg.create_viewport(
                title="ColorTracker Algorithm V3",
                width=self._viewport_original_width,
                height=self._viewport_original_height,
                x_pos=self._viewport_original_pos[0],
                y_pos=self._viewport_original_pos[1],
                decorated=self._viewport_original_decorated,
                always_on_top=self._viewport_original_always_on_top,
            )
            dpg.setup_dearpygui()

            # Configure app with available options only
            try:
                dpg.configure_app(manual_callback_management=False)
            except Exception:
                # Fallback for older versions
                pass

            self.logger.debug("DearPyGUI interface initialized successfully")
        except Exception as e:
            self.logger.critical(f"CRITICAL: Failed to initialize DearPyGUI viewport or setup. {e}")
            # We raise here because the app cannot run without the GUI
            raise

        # 13. Mouse Wheel Handler
        with dpg.handler_registry():
            dpg.add_mouse_wheel_handler(callback=self._on_mouse_wheel)

    def _on_mouse_wheel(self, sender, app_data):
        """Handle mouse wheel for magnifier zoom"""
        if not self.picking_mode:
            return

        # app_data is usually +1 or -1 (or multiples thereof)
        # Scroll UP (+): Zoom IN (smaller capture area, larger pixels)
        # Scroll DOWN (-): Zoom OUT (larger capture area, smaller pixels)

        step = 1 if app_data > 0 else -1
        new_index = (
            self._zoom_index - step
        )  # Reverse direction: Scroll Up = Smaller Index = Smaller Capture = More Zoom

        # Clamp index
        if 0 <= new_index < len(self._zoom_levels):
            self._zoom_index = new_index
            self._zoom_level = self._zoom_levels[self._zoom_index]
            self._magnifier_scale = self._magnifier_size // self._zoom_level

            # Re-draw the grid overlay
            self._refresh_magnifier_grid()

    def _refresh_magnifier_grid(self):
        """Redraw grid lines and UI overlays based on new zoom level"""
        if not dpg.does_item_exist("mag_drawlist"):
            return

        dpg.delete_item("mag_drawlist", children_only=True)

        px_size = self._magnifier_scale
        center_f = self._magnifier_size / 2
        ox, oy = 20, 10  # Manual offset for magnifier centering

        # 1. Draw Pixel Grid (Very Subtle)
        grid_alpha = 20  # Reduced for clarity
        for i in range(self._zoom_level + 1):
            line_pos = i * px_size
            dpg.draw_line(
                [line_pos + ox, oy],
                [line_pos + ox, self._magnifier_size + oy],
                color=(255, 255, 255, grid_alpha),
                parent="mag_drawlist",
            )
            dpg.draw_line(
                [ox, line_pos + oy],
                [self._magnifier_size + ox, line_pos + oy],
                color=(255, 255, 255, grid_alpha),
                parent="mag_drawlist",
            )

        # 2. Circular Bezel & Masking (The "Lens" look)
        # Draw a thick outer ring that hides the square corners
        mask_color = (30, 30, 35, 255)
        lens_radius = self._magnifier_size / 2
        bezel_thickness = 40.0

        # Draw dark outer masking to force circular shape
        dpg.draw_circle(
            [center_f + ox, center_f + oy],
            lens_radius + bezel_thickness / 2,
            color=mask_color,
            thickness=bezel_thickness,
            parent="mag_drawlist",
        )

        # Draw a sharp white inner border for the lens
        dpg.draw_circle(
            [center_f + ox, center_f + oy], lens_radius, color=(255, 255, 255, 200), thickness=1.5, parent="mag_drawlist"
        )

        # 3. Surgical Crosshair (Centered on the target pixel)
        center_idx = self._zoom_level // 2
        cs = px_size * center_idx
        ce = cs + px_size
        mid = (cs + ce) / 2
        mx, my = mid + ox, mid + oy

        cross_color = (0, 255, 255, 255)  # Precision Cyan
        gap = 4  # Gap in the middle to see the color clearly
        ext = 12  # Length of crosshair lines

        # Horizontal lines
        dpg.draw_line([mx - gap - ext, my], [mx - gap, my], color=cross_color, thickness=1, parent="mag_drawlist")
        dpg.draw_line([mx + gap, my], [mx + gap + ext, my], color=cross_color, thickness=1, parent="mag_drawlist")

        # Vertical lines
        dpg.draw_line([mx, my - gap - ext], [mx, my - gap], color=cross_color, thickness=1, parent="mag_drawlist")
        dpg.draw_line([mx, my + gap], [mx, my + gap + ext], color=cross_color, thickness=1, parent="mag_drawlist")

        # Tiny dot for exact center
        dpg.draw_circle([mx, my], 1.0, color=cross_color, fill=cross_color, parent="mag_drawlist")

    def start_algo_key(self, sender=None, app_data=None):
        """Start algorithm when PageUp key is pressed with optimized response"""
        if not self.config.enabled:
            self.config.enabled = True
            self.logger.info("PageUp pressed - Starting color tracking algorithm")
            self.start_algo()
        else:
            self.logger.debug("PageUp pressed - Algorithm already running")

    def stop_algo_key(self, sender=None, app_data=None):
        """Stop algorithm when PageDown key is pressed with optimized response"""
        if self.config.enabled:
            self.config.enabled = False
            self.logger.info("PageDown pressed - Stopping color tracking algorithm")
            self.stop_algo()
        else:
            self.logger.debug("PageDown pressed - Algorithm already stopped")

    def toggle_algo(self, sender=None, app_data=None):
        """Toggle algorithm on/off with immediate UI feedback"""
        old_state = self.config.enabled
        self.config.enabled = not self.config.enabled
        self.logger.debug(f"Algorithm toggle requested: {old_state} -> {self.config.enabled}")

        # Immediate UI feedback
        self._update_ui_state()

        if self.config.enabled:
            self.logger.debug("Algorithm enabled - starting algorithm thread")
            self.start_algo()
        else:
            self.logger.debug("Algorithm disabled - stopping algorithm thread")
            self.stop_algo()

    def _update_ui_state(self):
        """Update UI state with optimized caching"""
        current_time = time.time()
        if current_time - self._last_ui_update < self._ui_update_interval:
            return

        self._last_ui_update = current_time

        # Update status text with caching
        if hasattr(self, "status_text"):
            if "status_text" not in self._gui_cache:
                self._gui_cache["status_text"] = dpg.does_item_exist(self.status_text)

            if self._gui_cache["status_text"]:
                if self.config.enabled:
                    dpg.set_value(self.status_text, "Status: Active")
                    dpg.configure_item(self.status_text, color=(0, 255, 0))
                else:
                    dpg.set_value(self.status_text, "Status: Idle")
                    dpg.configure_item(self.status_text, color=(255, 255, 255))

        # Update enabled checkbox with caching
        if hasattr(self, "enabled_checkbox"):
            if "enabled_checkbox" not in self._gui_cache:
                self._gui_cache["enabled_checkbox"] = dpg.does_item_exist(self.enabled_checkbox)

            if self._gui_cache["enabled_checkbox"]:
                dpg.set_value(self.enabled_checkbox, self.config.enabled)

    def start_algo(self):
        """Start the algorithm in a separate thread with optimized startup"""
        if not self.running:
            self.logger.debug("Starting algorithm thread...")
            self.running = True
            self.thread = threading.Thread(target=self.algo_loop, daemon=True)
            self.thread.start()
            self.logger.info("Color tracking algorithm started successfully")
            self.logger.debug(f"Algorithm thread ID: {self.thread.ident}, Target FPS: {self.config.target_fps}")

            # Immediate UI state update
            self._update_ui_state()
        else:
            self.logger.debug("Algorithm start requested but already running")

    def stop_algo(self):
        """Stop the algorithm thread with optimized shutdown"""
        if self.running:
            self.logger.debug("Stopping algorithm thread...")
            self.running = False
            if self.thread:
                self.logger.debug(f"Waiting for thread {self.thread.ident} to join (timeout: 1.0s)")
                self.thread.join(timeout=1.0)
                if self.thread.is_alive():
                    self.logger.warning("Algorithm thread did not stop within timeout period")
                else:
                    self.logger.debug("Algorithm thread stopped cleanly")
            self.logger.info("Color tracking algorithm stopped successfully")

            # Immediate UI state update
            self._update_ui_state()
        else:
            self.logger.debug("Algorithm stop requested but not currently running")

    def toggle_debug_console(self, sender=None, app_data=None):
        """Toggle the debug console visibility with F12 key"""
        if hasattr(self, "logger") and self.logger.debug_console_enabled:
            new_state = self.logger.toggle_debug_console()
            state_text = "shown" if new_state else "hidden"
            self.logger.info(f"Debug console {state_text} - Press F12 to toggle")
        else:
            # Fallback message if debug console is not enabled
            print("Debug console not enabled - enable debug_mode in config to use F12 debug console")

    def algo_loop(self):
        """Main algorithm loop with optimized performance and reduced logging"""
        # Enable high-precision timing on Windows
        is_win = sys.platform == "win32"
        if is_win:
            try:
                ctypes.windll.winmm.timeBeginPeriod(1)
            except Exception:
                pass

        try:
            self._algo_loop_internal()
        finally:
            if is_win:
                try:
                    ctypes.windll.winmm.timeEndPeriod(1)
                except Exception:
                    pass

    def _algo_loop_internal(self):
        """Internal loop logic with optimized performance for ultra-high FPS"""
        self.logger.debug("Algorithm loop started - beginning main detection and tracking cycle")
        loop_count = 0

        # Performance optimization: cache frequently used values
        config_enabled = self.config.enabled
        target_fps = self.config.target_fps
        frame_interval = 1.0 / target_fps

        # Ultra-precision timing setup
        self.start_time = time.perf_counter()
        self.last_fps_update = self.start_time

        # Local references to methods to avoid self. lookup overhead
        find_target = self.detection.find_target
        process_motion = self.motion_engine.process
        aim_at = self.movement.aim_at
        update_target_status = self._update_target_status
        update_fps_display = self._update_fps_display
        perf_monitor = self.perf_monitor

        # High-performance timing variables
        target_frame_time = frame_interval

        try:
            while self.running:
                loop_start_time = time.perf_counter()
                perf_monitor.start_probe("main_loop_active")
                loop_count += 1

                # Update cached config values periodically (less frequent for performance)
                if loop_count % 500 == 0:
                    config_enabled = self.config.enabled
                    target_fps = self.config.target_fps
                    new_frame_interval = 1.0 / max(1, target_fps)
                    if abs(new_frame_interval - frame_interval) > 0.0001:
                        frame_interval = new_frame_interval
                        target_frame_time = frame_interval
                    # Sync motion engine config cache
                    self.motion_engine.update_config()

                # Ultra-efficient FPS calculation (every 1 second for better responsiveness)
                current_time = time.perf_counter()

                # Use PerformanceMonitor for stats
                if current_time - self.last_fps_update >= 1.0:
                    stats = perf_monitor.get_stats()
                    self.fps = stats["fps"]
                    self.last_fps_update = current_time

                    # Log performance metrics periodically
                    if loop_count % 600 == 0 and hasattr(self, "logger"):
                        self.logger.debug(
                            f"Performance: {stats['fps']:.1f} FPS | "
                            f"Avg: {stats['avg_frame_ms']:.2f}ms | "
                            f"Max: {stats['worst_frame_ms']:.2f}ms | "
                            f"Missed: {int(stats['missed_frames'])}"
                        )
                        # Reset aggregate counters in monitor
                        perf_monitor.reset_aggregates()

                    # Update UI with rate limiting
                    update_fps_display()

                # Only run if enabled
                if config_enabled:
                    try:
                        # Step 1: Detect target
                        t0_detect = time.perf_counter()
                        target_found, target_x, target_y = find_target()
                        t1_detect = time.perf_counter()
                        perf_monitor.record_detection(t1_detect - t0_detect)

                        # Update target status with rate limiting (less frequent at high FPS)
                        if loop_count % 100 == 0:
                            update_target_status(target_found)

                        # Step 2: If target found, predict and move
                        if target_found:
                            try:
                                # Calculate motion (smoothing + prediction)
                                predicted_x, predicted_y = process_motion(target_x, target_y, target_frame_time)

                                # Move mouse to target
                                aim_at(predicted_x, predicted_y)
                            except Exception as move_error:
                                if loop_count % 500 == 0:
                                    self.logger.error(f"Movement subsystem error: {move_error}")

                    except Exception as detection_error:
                        if loop_count % 100 == 0:
                            self.logger.error(f"Detection subsystem fault: {detection_error}")

                # Ultra-precise frame timing without busy waiting
                frame_end_time = time.perf_counter()
                perf_monitor.stop_probe("main_loop_active")
                actual_frame_time = frame_end_time - loop_start_time

                # Calculate precise sleep time
                sleep_time = target_frame_time - actual_frame_time

                # Record performance metrics for every frame (fix for 0 FPS stats)
                perf_monitor.record_frame(actual_frame_time, missed=(sleep_time <= 0))

                # Use hybrid precision sleep
                if sleep_time > 0:
                    self._smart_sleep(sleep_time, loop_start_time + target_frame_time)

                # No else block needed for record_frame anymore

        except Exception as fatal_error:
            # Fatal errors should always be logged
            self.logger.critical(f"Fatal error in algorithm loop: {fatal_error}")

        finally:
            self.logger.debug(f"Algorithm loop ended after {loop_count} iterations")

    def _update_fps_display(self):
        """Update FPS display with caching"""
        if hasattr(self, "fps_text"):
            if "fps_text" not in self._gui_cache:
                self._gui_cache["fps_text"] = dpg.does_item_exist(self.fps_text)

            if self._gui_cache["fps_text"]:
                dpg.set_value(self.fps_text, f"FPS: {self.fps:.1f}")

    def _update_target_status(self, target_found):
        """Update target status with caching and rate limiting"""
        # Only update if status changed
        if self._target_status_cache == target_found:
            return

        self._target_status_cache = target_found

        # Use the GUI update method if available
        if hasattr(self, "update_target_status"):
            self.update_target_status(target_found)

    def start_picking_mode(self, sender=None, app_data=None):
        """Enter Eyedropper mode with a global magnifier that follows the mouse"""
        if self.picking_mode:
            return

        self.logger.info("Entering Eyedropper mode - Click anywhere to pick color, ESC to cancel")

        # Save original viewport state
        self._viewport_original_pos = dpg.get_viewport_pos()
        self._viewport_original_width = dpg.get_viewport_width()
        self._viewport_original_height = dpg.get_viewport_height()

        # Pause tracking if running
        self._was_running_before_pick = self.config.enabled
        if self.config.enabled:
            self.stop_algo_key()
            self.config.enabled = False

        self.picking_mode = True
        self._picking_sct = None  # Initialized in main loop to prevent threading issues

        # Initialize Magnifier UI
        self._setup_magnifier_ui()

        # Transform viewport into a global magnifier window
        mag_w = self._magnifier_size + 40
        mag_h = self._magnifier_size + 110
        dpg.configure_viewport(
            "ColorTracker Algorithm V3", width=mag_w, height=mag_h, decorated=False, always_on_top=True, resizable=False
        )

        # Update status UI
        if hasattr(self, "status_text") and dpg.does_item_exist(self.status_text):
            dpg.set_value(self.status_text, "Status: Picking Color...")
            dpg.configure_item(self.status_text, color=(255, 165, 0))

    def _setup_magnifier_ui(self):
        """Create the Precision Lens magnifier window and texture"""
        if dpg.does_alias_exist("magnifier_window"):
            dpg.delete_item("magnifier_window")
        if dpg.does_alias_exist("magnifier_texture"):
            dpg.delete_item("magnifier_texture")

        # Create dynamic texture (Full resolution 160x160)
        default_data = [0.0] * (self._magnifier_size * self._magnifier_size * 4)

        with dpg.texture_registry():
            self._magnifier_texture = dpg.add_dynamic_texture(
                width=self._magnifier_size,
                height=self._magnifier_size,
                default_value=default_data,
                tag="magnifier_texture",
            )

        # Create floating window
        mag_w = self._magnifier_size + 40
        mag_h = self._magnifier_size + 110

        with dpg.window(
            tag="magnifier_window",
            no_title_bar=True,
            no_resize=True,
            no_move=True,
            no_scrollbar=True,
            no_background=True,  # Fully transparent window, we draw our own backgrounds
            width=mag_w,
            height=mag_h,
            show=True,
        ):
            # 1. Main Drawlist for everything
            with dpg.drawlist(width=mag_w, height=mag_h, tag="mag_parent_drawlist"):
                # Shadow/Glow for the lens
                dpg.draw_circle(
                    [mag_w / 2, self._magnifier_size / 2 + 10],
                    self._magnifier_size / 2 + 2,
                    color=(0, 0, 0, 100),
                    thickness=4,
                )

                # Texture background
                dpg.draw_image(
                    "magnifier_texture",
                    [20, 10],
                    [20 + self._magnifier_size, 10 + self._magnifier_size],
                )

                # Grid and overlays drawlist (centered on image)
                dpg.add_draw_node(tag="mag_drawlist")
                # We'll use translation later to align this node with the image

                # PILL-SHAPED INFO PANEL (Background)
                pill_y = self._magnifier_size + 25
                pill_h = 60
                dpg.draw_rectangle(
                    [20, pill_y],
                    [mag_w - 20, pill_y + pill_h],
                    color=(40, 40, 45, 240),
                    fill=(30, 30, 35, 230),
                    rounding=15,
                    thickness=1.5,
                    tag="mag_pill_bg",
                )

            # 2. Text elements (positioned over the pill)
            with dpg.group(pos=[35, self._magnifier_size + 32]):
                with dpg.group(horizontal=True):
                    self._magnifier_hex_text = dpg.add_text("#FFFFFF", color=(255, 255, 255))
                    dpg.add_spacer(width=10)
                    self._magnifier_coord_text = dpg.add_text("(0, 0)", color=(150, 150, 150))

                with dpg.group(horizontal=True):
                    self._magnifier_rgb_text = dpg.add_text("255, 255, 255", color=(201, 0, 141))

        # Initial grid draw
        self._refresh_magnifier_grid()

    def _update_picking_logic(self):
        """Handle Eyedropper logic in the GUI thread"""
        if not self.picking_mode:
            return

        # Lazy initialization of MSS in the main thread to avoid Threading Violations
        if self._picking_sct is None:
            try:
                # Disable cursor capture to avoid capturing cursor shadow/pixels
                self._picking_sct = mss.mss(with_cursor=False)
            except Exception as e:
                self.logger.error(f"Failed to initialize MSS for Eyedropper: {e}")
                self._exit_picking_mode(cancelled=True)
                return

        # Get current cursor position for real-time feedback
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))

        # Real-time preview feedback
        try:
            # Magnifier Capture: Grab a small region around the cursor
            half_zoom = self._zoom_level // 2
            monitor = {
                "top": pt.y - half_zoom,
                "left": pt.x - half_zoom,
                "width": self._zoom_level,
                "height": self._zoom_level,
            }
            sct_img = self._picking_sct.grab(monitor)

            # Update Magnifier Texture using NumPy (Faster & Color Accurate)
            # mss returns BGRA on Windows. We need RGBA for DPG.
            img_bgra = np.array(sct_img)

            # 1. Convert BGRA to RGB (Drop Alpha, Swap B & R)
            # img_bgra is [Height, Width, 4] -> B, G, R, A
            # We want [Height, Width, 3] -> R, G, B
            img_rgb = img_bgra[:, :, :3][:, :, ::-1]

            # 2. Get Center Pixel Color (for labels)
            # Use the middle pixel of the captured 11x11 grid
            center_px = img_rgb[half_zoom, half_zoom]
            r, g, b = int(center_px[0]), int(center_px[1]), int(center_px[2])
            current_hex = f"#{r:02X}{g:02X}{b:02X}"

            # 3. Manual Nearest-Neighbor Upscaling
            # Repeat pixels to scale up (e.g., 11x11 -> 154x154)
            # scale=14
            img_large_rgb = np.repeat(np.repeat(img_rgb, self._magnifier_scale, axis=0), self._magnifier_scale, axis=1)

            # 4. Prepare Texture Data (RGBA, Normalized float 0.0-1.0)
            # Add Alpha channel (255) to the large image
            h, w, _ = img_large_rgb.shape
            alpha_channel = np.full((h, w, 1), 255, dtype=np.uint8)
            img_large_rgba = np.concatenate((img_large_rgb, alpha_channel), axis=2)

            # Normalize and flatten
            texture_data = (img_large_rgba.astype(np.float32) / 255.0).ravel()

            dpg.set_value("magnifier_texture", texture_data)

            # Set text color to exactly match the hovered pixel color
            text_color = [r, g, b]
            luminance = 0.299 * r + 0.587 * g + 0.114 * b

            # Ensure readability by dynamically adjusting the pill background color
            if dpg.does_item_exist("mag_pill_bg"):
                if luminance < 80:  # If the text color is too dark
                    # Switch to a light background for dark text
                    dpg.configure_item("mag_pill_bg", fill=(240, 240, 245, 230), color=(255, 255, 255, 240))
                else:
                    # Keep/Restore dark background for light text
                    dpg.configure_item("mag_pill_bg", fill=(30, 30, 35, 230), color=(40, 40, 45, 240))

            # Update labels with dynamic color matching the hovered pixel
            if dpg.does_item_exist(self._magnifier_coord_text):
                dpg.set_value(self._magnifier_coord_text, f"XY: ({pt.x}, {pt.y})")
            if dpg.does_item_exist(self._magnifier_hex_text):
                dpg.set_value(self._magnifier_hex_text, f"HEX: {current_hex}")
                dpg.configure_item(self._magnifier_hex_text, color=text_color)
            if dpg.does_item_exist(self._magnifier_rgb_text):
                dpg.set_value(self._magnifier_rgb_text, f"RGB: ({r}, {g}, {b})")
                dpg.configure_item(self._magnifier_rgb_text, color=text_color)

            # Update button label with real-time feedback
            if dpg.does_item_exist("btn_pick_color"):
                dpg.configure_item("btn_pick_color", label=f"PICKING: {current_hex} (ESC to Cancel)")

            # QoL: Update the large preview box in the UI real-time if it exists
            if dpg.does_item_exist("theme_color_preview_val"):
                dpg.configure_item("theme_color_preview_val", value=[r, g, b, 255])
            if dpg.does_item_exist("theme_color_preview_hover"):
                dpg.configure_item("theme_color_preview_hover", value=[r, g, b, 255])
            if dpg.does_item_exist("theme_color_preview_active"):
                dpg.configure_item("theme_color_preview_active", value=[r, g, b, 255])

            # Position magnifier window near cursor but offset so it doesn't block picking
            # We use ScreenInfo or dpg.get_viewport_width to keep it on screen
            sw, sh = ScreenInfo.get_screen_size()
            mag_w = self._magnifier_size + 40
            mag_h = self._magnifier_size + 110

            # Default offset (bottom right)
            off_x, off_y = 25, 25
            if pt.x + off_x + mag_w > sw:
                off_x = -mag_w - 50
            if pt.y + off_y + mag_h > sh:
                off_y = -mag_h - 50

            # Move the entire OS viewport to follow the mouse
            vx = float(pt.x + off_x)
            vy = float(pt.y + off_y)
            dpg.set_viewport_pos([vx, vy])

            # Keep internal window at 0,0 relative to viewport
            dpg.set_item_pos("magnifier_window", [0, 0])

            # Drawing offset is now handled manually in _refresh_magnifier_grid

        except Exception:
            # Fail silently for real-time preview
            r, g, b = 0, 0, 0

        # Check for ESC key (cancel)
        if ctypes.windll.user32.GetAsyncKeyState(0x1B) & 0x8000:
            self._exit_picking_mode(cancelled=True)
            return

        # Check for Mouse Click (confirm)
        if ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
            self.config.target_color = (r << 16) | (g << 8) | b
            self.logger.info(f"Color picked: {hex(self.config.target_color)} (R:{r}, G:{g}, B:{b})")
            self._exit_picking_mode(cancelled=False)
            return

        # Keyboard Precision: Move cursor with arrow keys (1px)
        # 0x25: LEFT, 0x26: UP, 0x27: RIGHT, 0x28: DOWN
        dx, dy = 0, 0
        if ctypes.windll.user32.GetAsyncKeyState(0x25) & 0x8000:
            dx = -1
        if ctypes.windll.user32.GetAsyncKeyState(0x27) & 0x8000:
            dx = 1
        if ctypes.windll.user32.GetAsyncKeyState(0x26) & 0x8000:
            dy = -1
        if ctypes.windll.user32.GetAsyncKeyState(0x28) & 0x8000:
            dy = 1

        if dx != 0 or dy != 0:
            ctypes.windll.user32.SetCursorPos(pt.x + dx, pt.y + dy)
            time.sleep(0.05)  # Prevent runaway movement

    def _exit_picking_mode(self, cancelled=False):
        """Exit Eyedropper mode and restore state"""
        if self._picking_sct:
            self._picking_sct.close()
        self._picking_sct = None
        self.picking_mode = False

        # Restore viewport to original state
        dpg.configure_viewport(
            "ColorTracker Algorithm V3",
            width=self._viewport_original_width,
            height=self._viewport_original_height,
            decorated=self._viewport_original_decorated,
            always_on_top=self._viewport_original_always_on_top,
            resizable=True,
        )
        # Ensure we pass a list of floats to satisfy type checker
        rvx = float(self._viewport_original_pos[0])
        rvy = float(self._viewport_original_pos[1])
        dpg.set_viewport_pos([rvx, rvy])

        # Hide/Cleanup Magnifier
        if dpg.does_item_exist("magnifier_window"):
            dpg.hide_item("magnifier_window")

        # Restore button label
        if dpg.does_item_exist("btn_pick_color"):
            dpg.configure_item("btn_pick_color", label="Pick Color from Screen")

        if cancelled:
            self.logger.info("Eyedropper mode cancelled by user")
            # Re-sync UI with saved config
            if hasattr(self, "refresh_ui_from_config"):
                self.refresh_ui_from_config()
        else:
            # Re-sync UI with new color
            if hasattr(self, "refresh_ui_from_config"):
                self.refresh_ui_from_config()
            self.config.save()

        # Restore tracking if it was running
        if hasattr(self, "_was_running_before_pick") and self._was_running_before_pick:
            self.config.enabled = True
            self.start_algo()

        # Update status UI
        self._update_ui_state()

    def _smart_sleep(self, duration: float, target_time: float):
        """Hybrid precision sleep: Fused sleep and spin-wait"""
        if duration <= 0:
            return

        # 1. Yield-based sleep for the majority of the duration (imprecise)
        if duration > 0.002:
            time.sleep(duration - 0.0015)

        # 2. High-precision spin-wait for the final ~1.5ms
        while time.perf_counter() < target_time:
            pass

    def run(self):
        """Start the DearPyGui main loop with performance optimizations"""
        self.logger.info("Launching GUI main loop...")
        dpg.show_viewport()

        self.start_time = time.time()
        self.last_fps_update = self.start_time

        # Main GUI Loop
        while dpg.is_dearpygui_running():
            self.frame_count += 1

            # Step 1: Update picking logic if active
            if self.picking_mode:
                self._update_picking_logic()

            # Step 2: Handle performance monitoring and UI updates
            current_time = time.time()

            # Update analytics graphs and metrics
            if current_time - self._last_analytics_update >= self._analytics_update_interval:
                if hasattr(self, "update_analytics"):
                    self.update_analytics()
                self._last_analytics_update = current_time

            # Render frame
            dpg.render_dearpygui_frame()

        self.logger.info("GUI loop terminated. Shutting down systems...")
        self.stop_algo()

        self.logger.debug("Saving configuration...")
        self.config.save()
        self.logger.debug("Destroying DearPyGUI context...")
        dpg.destroy_context()
        self.logger.info(f"Application closed successfully after {self.frame_count} GUI frames")


if __name__ == "__main__":
    app = None
    try:
        app = ColorTrackerAlgo()
        app.run()
    except KeyboardInterrupt:
        print("\nShutdown requested by user (Ctrl+C). Saving and exiting...")
    except Exception as e:
        print(f"Critical Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if app and hasattr(app, "config"):
            try:
                app.config.save()
                print("Final configuration saved successfully.")
            except Exception as e:
                print(f"Failed to save final configuration: {e}")
