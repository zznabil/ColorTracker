#!/usr/bin/env python3

"""
Keyboard Listener Utility

Handles keyboard input for hotkeys and rebinding.
"""

import threading
from collections.abc import Callable

from pynput import keyboard


class KeyboardListener:
    """Handles keyboard input for hotkeys"""

    def __init__(self, config):
        """
        Initialize the keyboard listener

        Args:
            config: Configuration object with hotkey settings
        """
        self.config = config
        self._lock = threading.Lock()

        # Callback functions
        self.callbacks = {}

        # Listener state
        self.running = False
        self.listener = None

        # Binding mode state
        self._bind_mode = False
        self._bind_callback = None

    def start(self):
        """
        Start the keyboard listener
        """
        with self._lock:
            if not self.running:
                self.running = True
                self.listener = keyboard.Listener(on_press=self._on_key_press, on_release=self._on_key_release)
                self.listener.daemon = True
                self.listener.start()

    def stop(self):
        """
        Stop the keyboard listener
        """
        with self._lock:
            if self.running and self.listener:
                self.running = False
                self.listener.stop()
                self.listener = None

    def register_callback(self, key_name: str, callback: Callable, on_press: bool = True):
        """
        Register a callback function for a key

        Args:
            key_name: Name of the key (e.g., 'alt', 'ctrl', 'f1')
            callback: Function to call when key is pressed/released
            on_press: Whether to trigger on key press (True) or release (False)
        """
        event_type = "press" if on_press else "release"
        key_name = key_name.lower()
        with self._lock:
            if key_name not in self.callbacks:
                self.callbacks[key_name] = {}

            self.callbacks[key_name][event_type] = callback

    def remove_callback(self, key_name: str, on_press: bool = True):
        """
        Remove a callback function for a key

        Args:
            key_name: Name of the key
            on_press: Whether to remove the press (True) or release (False) callback
        """
        event_type = "press" if on_press else "release"
        key_name = key_name.lower()
        with self._lock:
            if key_name in self.callbacks and event_type in self.callbacks[key_name]:
                del self.callbacks[key_name][event_type]
                # Clean up empty dicts
                if not self.callbacks[key_name]:
                    del self.callbacks[key_name]

    def listen_for_single_key(self, callback: Callable[[str], None]):
        """
        Listen for a single key press for rebinding purposes.
        blocks normal callbacks until a key is pressed.

        Args:
            callback: Function that receives the detected key name
        """
        self._bind_callback = callback
        self._bind_mode = True

    def _on_key_press(self, key):
        """
        Handle key press events

        Args:
            key: The key that was pressed
        """
        key_name = self._get_key_name(key)

        with self._lock:
            # Handle binding mode
            if self._bind_mode:
                if self._bind_callback:
                    # Call the binding callback
                    try:
                        self._bind_callback(key_name)
                    except Exception as e:
                        print(f"Error in binding callback: {e}")

                # Reset binding mode
                self._bind_mode = False
                self._bind_callback = None
                return

            if key_name in self.callbacks and "press" in self.callbacks[key_name]:
                try:
                    self.callbacks[key_name]["press"]()
                except Exception as e:
                    print(f"Error in hotkey callback (press): {e}")

    def _on_key_release(self, key):
        """
        Handle key release events

        Args:
            key: The key that was released
        """
        # Ignore release events in binding mode
        with self._lock:
            if self._bind_mode:
                return

        key_name = self._get_key_name(key)

        with self._lock:
            if key_name in self.callbacks and "release" in self.callbacks[key_name]:
                try:
                    self.callbacks[key_name]["release"]()
                except Exception as e:
                    print(f"Error in hotkey callback (release): {e}")

    def _get_key_name(self, key):
        """
        Get the name of a key

        Args:
            key: The key object from pynput

        Returns:
            String name of the key
        """
        try:
            # For special keys
            if hasattr(key, "name"):
                return key.name.lower()
            # For character keys
            else:
                return key.char.lower()
        except AttributeError:
            # If we can't get the name or character
            return str(key).lower()
