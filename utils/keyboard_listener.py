#!/usr/bin/env python3

"""
Keyboard Listener Utility

Handles keyboard input for hotkeys.
"""

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

        # Callback functions
        self.callbacks = {}

        # Listener state
        self.running = False
        self.listener = None

    def start(self):
        """
        Start the keyboard listener
        """
        if not self.running:
            self.running = True
            self.listener = keyboard.Listener(on_press=self._on_key_press, on_release=self._on_key_release)
            self.listener.daemon = True
            self.listener.start()

    def stop(self):
        """
        Stop the keyboard listener
        """
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
        event_type = 'press' if on_press else 'release'
        if key_name not in self.callbacks:
            self.callbacks[key_name] = {}

        self.callbacks[key_name][event_type] = callback

    def _on_key_press(self, key):
        """
        Handle key press events

        Args:
            key: The key that was pressed
        """
        key_name = self._get_key_name(key)

        if key_name in self.callbacks and 'press' in self.callbacks[key_name]:
            self.callbacks[key_name]['press']()

    def _on_key_release(self, key):
        """
        Handle key release events

        Args:
            key: The key that was released
        """
        key_name = self._get_key_name(key)

        if key_name in self.callbacks and 'release' in self.callbacks[key_name]:
            self.callbacks[key_name]['release']()

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
            if hasattr(key, 'name'):
                return key.name.lower()
            # For character keys
            else:
                return key.char.lower()
        except AttributeError:
            # If we can't get the name or character
            return str(key).lower()
