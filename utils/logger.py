#!/usr/bin/env python3

"""
Logger Utility

Provides logging functionality for the application with rate limiting and spam prevention.
"""

import hashlib
import logging
import os
import time
from collections import defaultdict, deque
from datetime import datetime
from logging.handlers import RotatingFileHandler


class Logger:
    """Enhanced logger with rate limiting, spam prevention, and DearPyGui debug integration"""

    def __init__(
        self, log_level=logging.INFO, log_to_file=False, max_log_size_mb=50, backup_count=5, enable_debug_console=False
    ):
        """
        Initialize the logger with rate limiting and spam prevention

        Args:
            log_level: Logging level (default: INFO)
            log_to_file: Whether to log to a file (default: False)
            max_log_size_mb: Maximum log file size in MB before rotation (default: 50)
            backup_count: Number of backup log files to keep (default: 5)
        """
        # Rate limiting and spam prevention
        self.message_counts = defaultdict(int)  # Track message frequency
        self.last_message_time = defaultdict(float)  # Track last occurrence time
        self.suppressed_messages = defaultdict(int)  # Track suppressed message counts
        self.rate_limit_window = 60  # Rate limit window in seconds
        self.max_messages_per_window = 10  # Max identical messages per window
        self.spam_threshold = 5  # Messages per second to consider spam
        self.last_spam_report = defaultdict(float)  # Last time we reported spam for a message type

        # Debug console and DearPyGui integration
        self.debug_console_enabled = enable_debug_console
        self.debug_window_tag = "debug_console"
        self.debug_log_buffer = deque(maxlen=1000)  # Keep last 1000 debug messages
        self.debug_rules = {
            "performance_monitoring": True,
            "system_state_changes": True,
            "target_detection_events": True,
            "mouse_movement_logs": False,  # Disabled by default to reduce spam
            "config_changes": True,
            "error_tracking": True,
            "gui_interactions": False,  # Disabled by default
            "memory_usage": True,
            "fps_tracking": True,
            "file_operations": True,
        }

        # Internal state for debug console
        self.debug_console_visible = False

        # Create logger
        self.logger = logging.getLogger("ColorTrackingAlgo")
        self.logger.setLevel(log_level)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)

        # Add console handler to logger
        self.logger.addHandler(console_handler)

        # Add file handler with rotation if requested
        if log_to_file:
            from utils.paths import get_app_dir

            logs_dir = os.path.join(get_app_dir(), "logs")

            # Create logs directory if it doesn't exist
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)

            # Create rotating file handler to prevent huge log files
            log_file = os.path.join(
                logs_dir,
                f"color tracking algo for single player games in development_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            )
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_log_size_mb * 1024 * 1024,  # Convert MB to bytes
                backupCount=backup_count,
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)

            # Add file handler to logger
            self.logger.addHandler(file_handler)

    def _should_log_message(self, message, level):
        """
        Determine if a message should be logged based on rate limiting

        Args:
            message: The message to check
            level: The logging level

        Returns:
            bool: True if message should be logged, False if suppressed
        """
        # Create a hash of the message for tracking
        message_hash = hashlib.md5(message.encode()).hexdigest()
        current_time = time.time()

        # Check if this is a spam message (too frequent)
        if message_hash in self.last_message_time:
            time_diff = current_time - self.last_message_time[message_hash]
            if time_diff < (1.0 / self.spam_threshold):  # Less than spam threshold interval
                self.suppressed_messages[message_hash] += 1
                return False

        # Update tracking
        if message_hash not in self.last_message_time:
            self.last_spam_report[message_hash] = current_time

        self.last_message_time[message_hash] = current_time
        self.message_counts[message_hash] += 1

        # Clean up old entries (older than rate limit window)
        cleanup_time = current_time - self.rate_limit_window
        keys_to_remove = []
        for key, last_time in self.last_message_time.items():
            if last_time < cleanup_time:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.last_message_time[key]
            if key in self.message_counts:
                del self.message_counts[key]
            if key in self.suppressed_messages:
                del self.suppressed_messages[key]

        return True

    def _setup_debug_console(self):
        """
        Setup DearPyGui debug console window for real-time logging
        """
        try:
            import dearpygui.dearpygui as dpg

            # Create debug console window
            with dpg.window(
                label="Debug Console", tag=self.debug_window_tag, width=600, height=400, pos=[100, 100], show=False
            ):
                # Add debug controls
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Clear Console", callback=lambda: dpg.set_value("debug_text", ""))
                    dpg.add_button(label="Save Debug Log", callback=self._save_debug_log)
                    dpg.add_checkbox(label="Auto-scroll", default_value=True, tag="debug_autoscroll")

                # Add debug rule toggles
                dpg.add_text("Debug Rules:")
                with dpg.group(horizontal=True):
                    for rule_name, default_value in self.debug_rules.items():
                        dpg.add_checkbox(
                            label=rule_name.replace("_", " ").title(),
                            default_value=default_value,
                            tag=f"debug_rule_{rule_name}",
                        )

                # Add debug output area
                dpg.add_input_text(tag="debug_text", multiline=True, readonly=True, width=-1, height=-1)

        except ImportError:
            self.logger.warning("DearPyGui not available - debug console disabled")
            self.debug_console_enabled = False

    def _save_debug_log(self):
        """
        Save current debug log buffer to file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"debug_log_{timestamp}.txt"

            with open(filename, "w") as f:
                f.write("Color Tracking Algo Debug Log\n")
                f.write(f"Generated: {datetime.now()}\n")
                f.write("=" * 50 + "\n\n")
                for log_entry in self.debug_log_buffer:
                    f.write(log_entry + "\n")

            self.logger.info(f"Debug log saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save debug log: {e}")

    def _update_debug_console(self, message, level):
        """
        Update DearPyGui debug console with new log message
        """
        if not self.debug_console_enabled:
            return

        try:
            import dearpygui.dearpygui as dpg

            # Add to buffer
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {level.upper()}: {message}"
            self.debug_log_buffer.append(formatted_message)

            # Update console display
            if dpg.does_item_exist("debug_text"):
                # Auto-scroll if enabled
                if dpg.get_value("debug_autoscroll"):
                    height = dpg.get_item_height("debug_text")
                    if height is not None:
                        dpg.set_y_scroll("debug_text", float(height))
        except Exception:
            pass  # Ignore errors to prevent logging loops

    def toggle_debug_rule(self, rule_name, enabled=None):
        """
        Toggle or set debug rule state

        Args:
            rule_name: Name of the debug rule
            enabled: True/False to set, None to toggle
        """
        if rule_name in self.debug_rules:
            if enabled is None:
                self.debug_rules[rule_name] = not self.debug_rules[rule_name]
            else:
                self.debug_rules[rule_name] = bool(enabled)

            self.info(f"Debug rule '{rule_name}' set to {self.debug_rules[rule_name]}")

    def _should_log_with_rule(self, message, rule_type):
        """
        Check if message should be logged based on debug rules

        Args:
            message: The message to check
            rule_type: Type of debug rule to check against

        Returns:
            bool: True if message should be logged
        """
        return self.debug_rules.get(rule_type, True)

    def _log_suppression_summary(self):
        """
        Log a summary of suppressed messages periodically
        """
        current_time = time.time()
        for message_hash, count in self.suppressed_messages.items():
            if count > 0 and (current_time - self.last_spam_report[message_hash]) > 30:  # Report every 30 seconds
                self.logger.info(f"Suppressed {count} duplicate log messages (hash: {message_hash[:8]}...)")
                self.suppressed_messages[message_hash] = 0
                self.last_spam_report[message_hash] = current_time

    def debug(self, message):
        """
        Log a debug message with aggressive rate limiting for spam messages

        Args:
            message: Message to log
        """
        # Aggressively suppress common spam messages in debug mode
        spam_patterns = [
            "no target found",
            "color tracking algo for single player games in development enabled - starting target detection",
            "loop #",
            "gui fps:",
            "gui frame #",
        ]

        # Check if this is a spam message
        is_spam = any(spam_phrase in message.lower() for spam_phrase in spam_patterns)

        if is_spam:
            # Create a simplified hash for the spam pattern (not the full message)
            for pattern in spam_patterns:
                if pattern in message.lower():
                    pattern_hash = hashlib.md5(pattern.encode()).hexdigest()
                    self.message_counts[pattern_hash] += 1

                    # Only log every 500th occurrence for "no target found" and similar
                    if pattern in [
                        "no target found",
                        "color tracking algo for single player games in development enabled - starting target detection",
                    ]:
                        if self.message_counts[pattern_hash] % 500 == 1:
                            self.logger.debug(
                                f"{message} [Suppressed {self.message_counts[pattern_hash] - 1} similar messages]"
                            )
                    # Only log every 1000th occurrence for loop messages
                    elif "loop #" in pattern or "gui" in pattern:
                        if self.message_counts[pattern_hash] % 1000 == 1:
                            self.logger.debug(
                                f"{message} [Suppressed {self.message_counts[pattern_hash] - 1} similar messages]"
                            )
                    return

        # For non-spam messages, use normal rate limiting
        if self._should_log_message(message, logging.DEBUG):
            self.logger.debug(message)
        self._log_suppression_summary()

    def show_debug_console(self):
        """
        Show the DearPyGui debug console window

        Returns:
            bool: True if console was shown, False if already visible or not enabled
        """
        if not self.debug_console_enabled:
            return False

        if not self.debug_console_visible:
            self._setup_debug_console()
            self.debug_console_visible = True
            return True
        return False

    def hide_debug_console(self):
        """
        Hide the DearPyGui debug console window

        Returns:
            bool: True if console was hidden, False if already hidden
        """
        if not self.debug_console_enabled or not self.debug_console_visible:
            return False

        try:
            import dearpygui.dearpygui as dpg

            if dpg.does_item_exist("debug_console"):
                dpg.delete_item("debug_console")
            self.debug_console_visible = False
            return True
        except ImportError:
            return False

    def toggle_debug_console(self):
        """
        Toggle the DearPyGui debug console window visibility

        Returns:
            bool: New visibility state (True=visible, False=hidden)
        """
        if not self.debug_console_enabled:
            return False

        if self.debug_console_visible:
            self.hide_debug_console()
            return False
        else:
            self.show_debug_console()
            return True

    def info(self, message):
        """
        Log an info message

        Args:
            message: Message to log
        """
        if self._should_log_message(message, logging.INFO):
            self.logger.info(message)
            self._update_debug_console(message, "info")
        self._log_suppression_summary()

    def warning(self, message):
        """
        Log a warning message

        Args:
            message: Message to log
        """
        if self._should_log_message(message, logging.WARNING):
            self.logger.warning(message)
            self._update_debug_console(message, "warning")
        self._log_suppression_summary()

    def error(self, message, rule_type=None):
        """
        Log an error message with rate limiting for known transient errors

        Args:
            message: Message to log
            rule_type: Debug rule type for filtering
        """
        if rule_type and not self._should_log_with_rule(message, rule_type):
            return

        # Handle known transient errors with reduced logging
        if any(
            error_type in message for error_type in ["ScreenShotError", "gdi32.GetDIBits() failed", "Detection error"]
        ):
            message_hash = hashlib.md5(message.encode()).hexdigest()
            self.message_counts[message_hash] += 1

            # Log first occurrence, then every 10th occurrence
            if self.message_counts[message_hash] == 1 or self.message_counts[message_hash] % 10 == 0:
                log_msg = f"{message} (occurrence #{self.message_counts[message_hash]})"
                self.logger.error(log_msg)
                self._update_debug_console(log_msg, "error")
                if self.message_counts[message_hash] > 1:
                    info_msg = "Additional occurrences of this error will be logged every 10th time"
                    self.logger.info(info_msg)
                    self._update_debug_console(info_msg, "info")
            return

        # For other errors, use normal rate limiting
        if self._should_log_message(message, logging.ERROR):
            self.logger.error(message)
            self._update_debug_console(message, "error")
        self._log_suppression_summary()

    def critical(self, message):
        """
        Log a critical message

        Args:
            message: Message to log
        """
        if self._should_log_message(message, logging.CRITICAL):
            self.logger.critical(message)
            self._update_debug_console(message, "critical")
        self._log_suppression_summary()

    def install_global_exception_handler(self):
        """
        Install a global exception handler to capture unhandled exceptions
        """
        import sys
        import traceback

        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            self.critical(f"Uncaught exception:\n{error_msg}")

            # Also print to stderr for console visibility
            sys.__stderr__.write(error_msg)

        sys.excepthook = handle_exception
