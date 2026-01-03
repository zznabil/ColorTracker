#!/usr/bin/env python3

"""
Color Tracking Algo for Single Player Games in Development - V3.4.1

Main entry point for the Color Tracking Algo application, orchestrated
for high-performance detection and responsive UI.
"""

import ctypes
import logging
import math
import threading
import time
from typing import Any

import dearpygui.dearpygui as dpg

from core.detection import DetectionSystem
from core.low_level_movement import LowLevelMovementSystem
from core.motion_engine import MotionEngine
from gui.main_window import setup_gui, update_picker_preview
from utils.config import Config
from utils.keyboard_listener import KeyboardListener
from utils.logger import Logger
from utils.performance_monitor import PerformanceMonitor
from utils.screen_info import ScreenInfo

# Make the application DPI aware to fix coordinate scaling issues on high-DPI monitors
try:
    if ctypes.windll.user32.SetProcessDPIAware():
        # Get scale factor for logging/debugging
        hdc = ctypes.windll.user32.GetDC(0)
        try:
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            print(f"System DPI Awareness enabled. DPI: {dpi} ({int(dpi / 96 * 100)}% scale)")
        finally:
            ctypes.windll.user32.ReleaseDC(0, hdc)
    else:
        print("System DPI Awareness failed to activate.")
except Exception as e:
    print(f"DPI Awareness initialization error: {e}")


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
    render_color_history: Any
    start_time: float
    # GUI elements set by setup_gui()
    color_r: int | str
    color_g: int | str
    color_b: int | str
    update_tolerance_preview: Any
    show_success_toast: Any

    def __init__(self):
        # State Initialization
        self._running_lock = threading.Lock()
        self._running = False
        self.thread = None
        self.fps = 0.0

        self.frame_count = 0
        self._target_status_cache = None

        # 1. Initialize DearPyGUI context first
        dpg.create_context()

        # 2. Load configuration early so other systems can use it
        self.config = Config()
        self.config.load()

        # Enable Stealth Mode (Hide from capture) if configured
        # WDA_EXCLUDEFROMCAPTURE = 0x11
        if getattr(self.config, "stealth_mode", False):
            try:
                # We'll set this after viewport creation in setup_gui
                pass
            except Exception:
                pass

        # 3. Create logger with optimized settings and startup safety
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

        # Define hotkey strings for comparison
        self.current_start_key = self.config.start_key
        self.current_stop_key = self.config.stop_key

        self._register_hotkeys()  # Register initial hotkeys
        self.keyboard.start()  # Start the background listener thread

        # 9. Picker mode state initialization
        self.picker_mode_active = False
        self.picker_current_color = 0x000000
        self.picker_cursor_x = 0
        self.picker_cursor_y = 0

        # 10. FOV Overlay state
        self.fov_overlay_enabled = getattr(self.config, "fov_overlay_enabled", False)

        # 11. Stealth Mode state
        self.stealth_mode_enabled = getattr(self.config, "stealth_mode", False)

        # 12. Viewport state for Global Magnifier
        self._viewport_original_width = 500
        self._viewport_original_height = 750
        self._viewport_original_pos = [100, 100]
        self._viewport_original_decorated = True
        self._viewport_original_always_on_top = False

        # 12. GUI Update interval
        self._ui_update_interval = 0.1
        self._last_ui_update = 0
        self._gui_cache = {}
        self._analytics_update_interval = 0.5
        self._last_analytics_update = 0

        # 13. Initialize GUI and viewport (MUST BE LAST)
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
                vsync=False,  # Disable VSync to unlock FPS
            )
            dpg.setup_dearpygui()

            # Configure app with available options only
            try:
                dpg.configure_app(manual_callback_management=False)
            except Exception:
                # Fallback for older versions
                pass

            self.logger.debug("DearPyGUI interface initialized successfully")

            # Wire embedded color picker button callbacks
            dpg.set_item_callback("btn_picker_start", lambda: self._start_picking_mode())
            dpg.set_item_callback("btn_picker_cancel", lambda: self._cancel_picking_mode())
            dpg.set_item_callback("picker_color_box", lambda: self._apply_picked_color())

            self.logger.debug("Embedded color picker integration completed")
        except Exception as e:
            self.logger.critical(f"CRITICAL: Failed to initialize DearPyGUI viewport or setup. {e}")
            # We raise here because the app cannot run without the GUI
            raise

    @property
    def running(self) -> bool:
        """Thread-safe access to running state."""
        with self._running_lock:
            return self._running

    @running.setter
    def running(self, value: bool):
        with self._running_lock:
            self._running = value

    def _register_hotkeys(self):
        """Register/Update hotkey callbacks in the listener."""
        # Remove old callbacks first (under lock in keyboard listener)
        self.keyboard.remove_callback(self.current_start_key)
        self.keyboard.remove_callback(self.current_stop_key)

        # Update current keys from config
        self.current_start_key = self.config.start_key
        self.current_stop_key = self.config.stop_key

        # Register new ones
        self.keyboard.register_callback(self.current_start_key, self.start_algo_key)
        self.keyboard.register_callback(self.current_stop_key, self.stop_algo_key)
        self.logger.debug(f"Hotkeys updated: Start={self.current_start_key}, Stop={self.current_stop_key}")

    def on_hotkey_rebound(self):
        """Called by GUI when a hotkey is changed to update the listener without restart."""
        self._register_hotkeys()

    def start_algo_key(self, sender=None, app_data=None):
        """Start algorithm handler with optimized response"""
        if not self.config.enabled:
            self.config.enabled = True
            self.logger.info(f"Hotkey [{self.current_start_key.upper()}] - Starting algorithm")
            self.start_algo()

    def stop_algo_key(self, sender=None, app_data=None):
        """Stop algorithm handler with optimized response"""
        if self.config.enabled:
            self.config.enabled = False
            self.logger.info(f"Hotkey [{self.current_stop_key.upper()}] - Stopping algorithm")
            self.stop_algo()

    def start_algo(self, sender=None, app_data=None):
        """Starts the color tracking algorithm thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._algo_loop_internal, daemon=True)
        self.thread.start()
        self._update_ui_state()

    def stop_algo(self, sender=None, app_data=None):
        """Stops the color tracking algorithm thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        self._update_ui_state()

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
        """Update UI state based on algorithm status with pulsing effect"""
        if not hasattr(self, "update_target_status"):
            return

        # Determine if we are running
        is_active = self.running

        # Add pulsing effect for Active state
        status_color = (255, 255, 255)
        if is_active:
            # Pulse green alpha or brightness using math.sin
            pulse = (math.sin(time.time() * 5) + 1) / 2  # 0 to 1
            green_val = int(150 + (105 * pulse))  # 150 to 255
            status_color = (0, green_val, 0)
            status_text = "Status: ACTIVE"
        elif self.config.enabled:
            status_color = (255, 255, 0)  # Yellow
            status_text = "Status: STANDBY"
        else:
            status_color = (200, 200, 200)  # Gray
            status_text = "Status: IDLE"

        # Update DearPyGui items if they exist
        if hasattr(self, "status_text") and dpg.does_item_exist(self.status_text):
            dpg.set_value(self.status_text, status_text)
            dpg.configure_item(self.status_text, color=status_color)

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
            if hasattr(self, "detection"):
                try:
                    self.detection.close()
                except Exception as e:
                    self.logger.error(f"Error closing detection system: {e}")
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

    def _start_picking_mode(self):
        """Enables color picking mode."""
        self.picker_mode_active = True
        self.logger.info("Color picker mode activated. Click anywhere to pick color.")

    def _cancel_picking_mode(self):
        """Disables color picking mode."""
        self.picker_mode_active = False
        self.logger.info("Color picker mode cancelled.")

    def _apply_picked_color(self):
        """Applies the currently picked color to the configuration."""
        self.picker_mode_active = False
        self.config.target_color = self.picker_current_color
        self.logger.info(f"Color applied: {hex(self.picker_current_color)}")
        if hasattr(self, "refresh_ui_from_config"):
            self.refresh_ui_from_config()

    def _get_pixel_at_cursor(self) -> tuple[int, int, int, int, int]:
        """Gets the RGB color and coordinates of the pixel under the cursor."""
        hdc = ctypes.windll.user32.GetDC(0)
        try:

            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            px, py = pt.x, pt.y
            color = ctypes.windll.gdi32.GetPixel(hdc, px, py)
            r = color & 0xFF
            g = (color >> 8) & 0xFF
            b = (color >> 16) & 0xFF
            return r, g, b, px, py
        finally:
            ctypes.windll.user32.ReleaseDC(0, hdc)

    def _apply_stealth_mode(self, enabled: bool):
        """Apply stealth mode (hide from capture)."""
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "ColorTracker Algorithm V3")
            if hwnd:
                # WDA_EXCLUDEFROMCAPTURE = 0x00000011 (Windows 10 2004+)
                # WDA_MONITOR = 0x00000001 (Prevents capture on monitor)
                affinity = 0x11 if enabled else 0x00
                ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, affinity)
                self.logger.info(f"Stealth mode {'activated' if enabled else 'deactivated'}")
        except Exception as e:
            self.logger.error(f"Failed to apply stealth mode: {e}")

    def run(self):
        """Start the DearPyGui main loop with performance optimizations"""
        self.logger.info("Launching GUI main loop...")
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)

        # Apply stealth mode once viewport is ready
        if self.stealth_mode_enabled:
            self._apply_stealth_mode(True)

        self.start_time = time.time()
        self.last_fps_update = self.start_time

        # Main GUI Loop
        while dpg.is_dearpygui_running():
            self.frame_count += 1
            current_time = time.time()

            # Pulse the status indicator if active (Phase 5 QoL)
            if current_time - self._last_ui_update >= self._ui_update_interval:
                self._update_ui_state()
                self._last_ui_update = current_time

            # Step 2: Update embedded color picker if active
            if self.picker_mode_active:
                r, g, b, cx, cy = self._get_pixel_at_cursor()
                self.picker_current_color = (r << 16) | (g << 8) | b
                self.picker_cursor_x = cx
                self.picker_cursor_y = cy
                update_picker_preview(self.picker_current_color, cx, cy)

                # Check for global left-click to apply color (Click-to-Apply UX)
                # GetAsyncKeyState returns negative if key is pressed
                VK_LBUTTON = 0x01
                VK_ESCAPE = 0x1B
                try:
                    left_click = ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000
                    escape_key = ctypes.windll.user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000
                    if left_click:
                        # Small debounce: wait for release to avoid multiple triggers
                        while ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000:
                            time.sleep(0.01)
                        self._apply_picked_color()
                    elif escape_key:
                        self._cancel_picking_mode()
                except Exception:
                    pass

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
