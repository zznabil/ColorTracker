#!/usr/bin/env python3

"""
Color Tracking Algo for Single Player Games in Development - V3.4.1

Main entry point for the Color Tracking Algo application, orchestrated
for high-performance detection and responsive UI.
"""

import ctypes
import gc
import logging
import sys
import threading
import time
from typing import Any

import dearpygui.dearpygui as dpg

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
    start_time: float

    def __init__(self):
        # Initialize DearPyGUI with performance optimizations
        dpg.create_context()
        # Configure app with available options only
        try:
            dpg.configure_app(manual_callback_management=False)
        except Exception:
            # Fallback for older versions
            pass

        # Create logger with optimized settings and startup safety
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

        # Load configuration
        self.config = Config()
        self.config.load()

        # Get screen information and log system details
        screen_width, screen_height = ScreenInfo.get_screen_size()
        self.config.screen_width = screen_width
        self.config.screen_height = screen_height
        self.logger.debug(f"Screen resolution detected: {screen_width}x{screen_height}")

        # Initialize performance monitor
        self.perf_monitor = PerformanceMonitor()

        # Initialize systems with optimized settings
        self.logger.debug("Initializing detection system...")
        self.detection = DetectionSystem(self.config, self.perf_monitor)
        self.logger.debug("Initializing unified motion engine...")
        self.motion_engine = MotionEngine(self.config)

        # Initialize movement system with optimized settings
        self.logger.debug("Initializing low-level movement system for game compatibility...")
        self.movement = LowLevelMovementSystem(self.config, self.perf_monitor)
        self.logger.debug("All core systems initialized successfully with low-level mouse input")

        # Initialize keyboard listener with optimized settings
        self.keyboard = KeyboardListener(self.config)
        # Register PageUp key to start the color tracking algorithm
        self.keyboard.register_callback(self.config.start_key, self.start_algo_key)
        # Register PageDown key to stop the color tracking algorithm
        self.keyboard.register_callback(self.config.stop_key, self.stop_algo_key)
        # Register F12 key to toggle debug console (only if debug mode is enabled)
        if hasattr(self.config, "debug_mode") and self.config.debug_mode:
            self.keyboard.register_callback("f12", self.toggle_debug_console)

        # Setup GUI with optimized settings
        setup_gui(self)

        # Thread control with optimized settings
        self.running = False
        self.thread = None

        # Performance metrics with optimized tracking
        self.fps = 0
        self.last_frame_time = 0
        self.frame_count = 0
        self.last_fps_update = 0

        # UI responsiveness optimization
        self._ui_update_interval = 0.05  # 20 FPS for UI updates
        self._analytics_update_interval = 0.5  # 2 FPS for Analytics graphs
        self._last_ui_update = 0
        self._last_analytics_update = 0
        self._target_status_cache = None

        # Cache frequently accessed GUI items
        self._gui_cache = {}

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

        # ULTRATHINK: Disable automatic garbage collection to prevent non-deterministic pauses
        # We will manually collect periodically in the logging block
        gc.disable()

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
        update_target_status = self._update_target_status
        update_fps_display = self._update_fps_display
        perf_monitor = self.perf_monitor
        move_to_target = self.move_to_target

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
                    # Sync movement engine config cache
                    self.movement.update_config()

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
                        # ULTRATHINK: Manual Garbage Collection
                        # Perform a generation 1 collection to clean up young objects without full stop-the-world
                        gc.collect(1)

                        # Reset aggregate counters in monitor
                        perf_monitor.reset_aggregates()

                    # Update UI with rate limiting
                    update_fps_display()

                # Only run if enabled
                if config_enabled:
                    try:
                        # Step 1: Detect target
                        # Hoist version check to main loop to avoid lookups in detection
                        current_config_version = getattr(self.config, "_version", 0)

                        t0_detect = time.perf_counter()
                        target_found, target_x, target_y = find_target(current_config_version)
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
                                move_to_target(predicted_x, predicted_y)
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
            # Re-enable GC when loop exits
            gc.enable()
            self.logger.debug(f"Algorithm loop ended after {loop_count} iterations")

    def move_to_target(self, x: int, y: int) -> None:
        """
        Delegates to movement system.
        Thread-safe wrapper for GUI/Sage parity.
        """
        self.movement.move_to_target(x, y)

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

    def _smart_sleep(self, duration: float, target_time: float | None = None) -> None:
        """
        Hybrid precise sleep: uses time.sleep for bulk waiting and busy-wait for final precision.

        Args:
            duration: Total seconds to sleep.
            target_time: Absolute timestamp (time.perf_counter) to wake up at.
                         If None, calculated from current time + duration.
        """
        if duration <= 0:
            return

        if target_time is None:
            target_time = time.perf_counter() + duration

        # ULTRATHINK OPTIMIZATION: Fixed slack time for consistent precision
        # Use sleep for longer periods (bulk wait)
        # 1.5ms slack is safe for Windows scheduler variance (typically 1ms resolution with timeBeginPeriod)
        slack = 0.0015

        if duration > slack:
            time.sleep(duration - slack)

        # High-precision spin wait for the remaining time
        while time.perf_counter() < target_time:
            # Minimal CPU usage - just yield to OS scheduler if needed, but here we spin
            # Check running flag to allow fast exit
            if not self.running:
                break

    def run(self):
        """Run the application with optimized UI responsiveness"""
        self.logger.debug("Starting application run sequence...")

        # Start keyboard listener
        self.logger.debug("Starting keyboard listener...")
        self.keyboard.start()
        self.logger.debug(
            f"Keyboard listener started - monitoring hotkeys: {self.config.start_key} (start), {self.config.stop_key} (stop)"
        )

        # Create viewport window with optimized settings
        self.logger.debug("Creating DearPyGUI viewport...")
        dpg.create_viewport(title="ColorTracker Algorithm V3", width=480, height=730)
        self.logger.debug("Setting up DearPyGUI context...")
        dpg.setup_dearpygui()
        self.logger.debug("Showing viewport window...")
        dpg.show_viewport()

        # Set primary window with optimized settings
        self.logger.debug("Setting primary window to main_window...")
        dpg.set_primary_window("main_window", True)
        self.logger.info("GUI initialized successfully - entering main loop")

        # Start the main loop with optimized frame timing
        frame_count = 0
        gui_start_time = time.perf_counter()
        last_frame_time = time.perf_counter()
        target_gui_fps = 60  # Target 60 FPS for GUI
        gui_frame_interval = 1.0 / target_gui_fps

        while dpg.is_dearpygui_running():
            current_time = time.perf_counter()

            # Update GUI with latest data at consistent frame rate
            if current_time - last_frame_time >= gui_frame_interval:
                frame_count += 1

                # Update FPS display with caching
                self._update_fps_display()

                # Update UI state
                self._update_ui_state()

                # Update Analytics (Rate limited)
                if hasattr(self, "update_analytics"):
                    if current_time - self._last_analytics_update >= self._analytics_update_interval:
                        self.update_analytics()
                        self._last_analytics_update = current_time

                last_frame_time = current_time

                # Log GUI performance every 5 seconds
                if frame_count % 300 == 0:
                    gui_runtime = current_time - gui_start_time
                    gui_fps = frame_count / gui_runtime
                    self.logger.debug(f"GUI performance: {gui_fps:.1f} FPS over {gui_runtime:.1f}s")

            # Render frame with minimal delay
            dpg.render_dearpygui_frame()

        # Clean up with optimized shutdown
        self.logger.debug("DearPyGUI main loop ended - starting cleanup...")
        self.logger.debug("Stopping algorithm if running...")
        self.stop_algo()
        self.logger.debug("Stopping keyboard listener...")
        self.keyboard.stop()
        self.logger.debug("Saving configuration...")
        self.config.save()
        self.logger.debug("Destroying DearPyGUI context...")
        dpg.destroy_context()
        self.logger.info(f"Application closed successfully after {frame_count} GUI frames")


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
