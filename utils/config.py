#!/usr/bin/env python3

"""
Configuration Utility

Handles loading and saving configuration settings.
"""

import glob
import json
import os
import threading
import time
from typing import Any


class Config:
    """Handles loading and saving configuration settings with self-healing capabilities"""

    # Type Hints for attributes
    screen_width: int
    screen_height: int
    target_color: int
    color_tolerance: int
    search_area: int
    fov_x: int
    fov_y: int
    aim_point: int
    head_offset: int
    leg_offset: int
    motion_min_cutoff: float
    motion_beta: float
    prediction_scale: float
    start_key: str
    stop_key: str
    target_fps: int
    enabled: bool
    debug_mode: bool
    config_file: str
    # Default configuration schema for validation and self-healing
    DEFAULT_CONFIG = {
        "screen_width": {"type": int, "default": 1920, "min": 640, "max": 7680},
        "screen_height": {"type": int, "default": 1080, "min": 480, "max": 4320},
        "target_color": {"type": int, "default": 0xC9008D},
        "color_tolerance": {"type": int, "default": 10, "min": 0, "max": 100},
        "search_area": {"type": int, "default": 100, "min": 10, "max": 1000},
        "fov_x": {"type": int, "default": 50, "min": 10, "max": 500},
        "fov_y": {"type": int, "default": 50, "min": 10, "max": 500},
        "aim_point": {"type": int, "default": 1, "min": 0, "max": 2},
        "head_offset": {"type": int, "default": 20, "min": 0, "max": 200},
        "leg_offset": {"type": int, "default": 30, "min": 0, "max": 200},
        "motion_min_cutoff": {"type": float, "default": 0.05, "min": 0.001, "max": 1.0},
        "motion_beta": {"type": float, "default": 0.05, "min": 0.001, "max": 1.0},
        "prediction_scale": {"type": float, "default": 1.0, "min": 0.0, "max": 10.0},
        "start_key": {"type": str, "default": "page_up"},
        "stop_key": {"type": str, "default": "page_down"},
        "target_fps": {"type": int, "default": 240, "min": 30, "max": 1000},
        "enabled": {"type": bool, "default": False},
        "debug_mode": {"type": bool, "default": False},
    }

    def __init__(self):
        """
        Initialize configuration with default values
        """
        # Apply defaults from schema
        for key, schema in self.DEFAULT_CONFIG.items():
            setattr(self, key, schema["default"])

        # Internal state
        self.config_file = "config.json"
        self.profiles_dir = "profiles"
        self._last_save_time = 0
        self._save_debounce_ms = 500
        self._save_timer = None
        self._lock = threading.Lock()

        # Load and validate saved configuration
        self.load()

    def validate(self, key: str, value: Any) -> Any:
        """
        Validates and repairs a specific configuration value

        Returns:
            The validated (and potentially corrected) value
        """
        if key not in self.DEFAULT_CONFIG:
            return value

        schema = self.DEFAULT_CONFIG[key]
        expected_type = schema["type"]

        # 1. Type Correction
        try:
            if expected_type is bool:
                if isinstance(value, str):
                    value = value.lower() in ("true", "1", "yes", "y", "on")
                else:
                    value = bool(value)
            elif expected_type is int:
                value = int(float(value))
            elif expected_type is float:
                value = float(value)
            elif expected_type is str:
                value = str(value)
        except (ValueError, TypeError):
            print(f"Config Repair: Invalid type for '{key}' (expected {expected_type.__name__}). Resetting to default.")
            return schema["default"]

        # 2. Range/Option Validation
        if expected_type in (int, float):
            if "min" in schema and value < schema["min"]:
                print(f"Config Repair: '{key}' ({value}) below minimum. Clamping to {schema['min']}.")
                value = schema["min"]
            if "max" in schema and value > schema["max"]:
                print(f"Config Repair: '{key}' ({value}) above maximum. Clamping to {schema['max']}.")
                value = schema["max"]

        if "options" in schema and value not in schema["options"]:
            print(f"Config Repair: '{key}' ({value}) not a valid option. Resetting to default.")
            return schema["default"]

        return value

    def load(self, filepath: str | None = None):
        """
        Load configuration from file if it exists with robust validation and repair
        """
        target_file = filepath if filepath else self.config_file

        if not os.path.exists(target_file):
            print(f"Config: {target_file} not found. Using defaults.")
            return

        try:
            with open(target_file, encoding="utf-8") as f:
                content = f.read()

            # Strip comments
            import re

            content = re.sub(r"//.*", "", content)
            content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

            config_data = json.loads(content)

            # Validate and apply each key
            for key in self.DEFAULT_CONFIG.keys():
                if key in config_data:
                    # Special handling for enum maps (legacy support)
                    value = config_data[key]
                    if key == "aim_point" and isinstance(value, str):
                        aim_point_map = {"Head": 0, "Body": 1, "Legs": 2, "Chest": 1, "Center": 1}
                        value = aim_point_map.get(value, 1)

                    # Validate and repair
                    validated_value = self.validate(key, value)
                    setattr(self, key, validated_value)
                else:
                    # Self-healing: Key missing in file, use default
                    print(f"Config Repair: Missing key '{key}' in {self.config_file}. Using default.")
                    setattr(self, key, self.DEFAULT_CONFIG[key]["default"])

            print(f"Configuration successfully loaded from {target_file}.")
        except Exception as e:
            print(f"Critical Error loading {target_file}: {e}. Falling back to safe defaults.")
            # Self-healing: Reset to defaults on critical failure
            if target_file == self.config_file:
                for key, schema in self.DEFAULT_CONFIG.items():
                    setattr(self, key, schema["default"])

    def save(self, filepath: str | None = None):
        """
        Save current configuration to file with detailed comments preserved
        """
        target_file = filepath if filepath else self.config_file

        # Cancel any pending save timer since we are saving now (only if saving main config)
        if target_file == self.config_file and self._save_timer:
            self._save_timer.cancel()
            self._save_timer = None

        try:
            with self._lock:
                # Create a dictionary of all configuration attributes
                config_data = {}
                for key, value in self.__dict__.items():
                    # Skip internal attributes
                    if not key.startswith("_") and key != "config_file" and key != "profiles_dir":
                        config_data[key] = value

                # Build the complete JSON content as a single string to avoid file handle issues
                json_content = "{\n"
            json_content += "    // === DISPLAY CONFIGURATION ===\n"
            json_content += "    // Screen resolution settings - MUST match your actual monitor resolution\n"
            json_content += f'    "screen_width": {config_data.get("screen_width", 1920)},     // Width in pixels (common: 1920, 2560, 3840)\n'
            json_content += f'    "screen_height": {config_data.get("screen_height", 1080)},    // Height in pixels (common: 1080, 1440, 2160)\n'
            json_content += "\n"

            json_content += "    // === COLOR DETECTION SETTINGS ===\n"
            json_content += "    // Target color to detect (RGB value as integer)\n"
            json_content += "    // Use color picker in GUI to set this value automatically\n"
            json_content += "    // Common target colors: Purple ~16733797, Red ~16711680, Pink ~16761035\n"
            json_content += f'    "target_color": {config_data.get("target_color", 16733797)},\n'
            json_content += "\n"
            json_content += "    // Color matching tolerance (0-100)\n"
            json_content += "    // Lower = more precise matching, Higher = more flexible matching\n"
            json_content += "    // Recommended: 10-20 for good lighting, 25-50 for variable lighting\n"
            json_content += f'    "color_tolerance": {config_data.get("color_tolerance", 15)},\n'
            json_content += "\n"

            json_content += "    // === DETECTION AREA SETTINGS ===\n"
            json_content += "    // Search area radius around crosshair (pixels)\n"
            json_content += "    // Larger = wider detection but slower performance\n"
            json_content += "    // Recommended: 50-150 depending on game and screen resolution\n"
            json_content += f'    "search_area": {config_data.get("search_area", 100)},\n'
            json_content += "\n"
            json_content += "    // Field of view for target detection (pixels from center)\n"
            json_content += "    // fov_x: horizontal detection range, fov_y: vertical detection range\n"
            json_content += "    // Smaller values = faster performance, larger = wider detection\n"
            json_content += "    // Recommended: 30-60 for most games\n"
            json_content += f'    "fov_x": {config_data.get("fov_x", 41)},\n'
            json_content += f'    "fov_y": {config_data.get("fov_y", 41)},\n'
            json_content += "\n"

            json_content += "    // === MOTION ENGINE SETTINGS ===\n"
            json_content += "    // 1 Euro Filter Settings\n"
            json_content += "    // motion_min_cutoff: Stabilization. Lower = More stable when slow. Rec: 0.001-0.1\n"
            json_content += f'    "motion_min_cutoff": {config_data.get("motion_min_cutoff", 0.05)},\n'
            json_content += "    // motion_beta: Responsiveness. Higher = Faster reaction. Rec: 0.001-0.1\n"
            json_content += f'    "motion_beta": {config_data.get("motion_beta", 0.05)},\n'
            json_content += "\n"
            json_content += "    // Prediction Status\n"
            json_content += "    // prediction_scale: Velocity prediction multiplier. 0.0 = Off.\n"
            json_content += f'    "prediction_scale": {config_data.get("prediction_scale", 1.0)},\n'
            json_content += "\n"
            json_content += "    // === TARGETING SETTINGS ===\n"
            json_content += "    // Target tracking point on detected objects\n"
            json_content += '    // Options: "Head", "Chest", "Legs", "Center"\n'
            json_content += "    // Head: Highest damage but smaller target\n"
            json_content += "    // Chest: Balanced damage and hit probability\n"
            json_content += "    // Legs: Largest target area but lower damage\n"
            aim_point_value = config_data.get("aim_point", "Body")
            if isinstance(aim_point_value, int):
                aim_point_map = {0: "Head", 1: "Body", 2: "Legs"}
                aim_point_value = aim_point_map.get(aim_point_value, "Body")
            json_content += f'    "aim_point": "{aim_point_value}",\n'
            json_content += "\n"
            json_content += "    // Pixel offset adjustments for tracking points\n"
            json_content += "    // head_offset: pixels above detected center for headshots\n"
            json_content += "    // leg_offset: pixels below detected center for leg shots\n"
            json_content += "    // Adjust based on game character models and your preference\n"
            json_content += f'    "head_offset": {config_data.get("head_offset", 20)},\n'
            json_content += f'    "leg_offset": {config_data.get("leg_offset", 30)},\n'
            json_content += "\n"

            json_content += "    // === CONTROL SETTINGS ===\n"
            json_content += "    // Hotkeys for color tracking algo for single player games in development control\n"
            json_content += "    // Available keys: F1-F12, page_up, page_down, insert, delete, home, end\n"
            json_content += "    // ctrl+key, alt+key, shift+key combinations also supported\n"
            json_content += f'    "start_key": "{config_data.get("start_key", "page_up")}",   // Key to activate color tracking algo for single player games in development\n'
            json_content += f'    "stop_key": "{config_data.get("stop_key", "page_down")}",  // Key to deactivate color tracking algo for single player games in development\n'
            json_content += "\n"

            json_content += "    // === PERFORMANCE SETTINGS ===\n"
            json_content += "    // Target frames per second for detection loop\n"
            json_content += "    // Higher FPS = more responsive but uses more CPU\n"
            json_content += (
                "    // Recommended: 60-120 for balanced performance, 240-480 for competitive, 960 for extreme\n"
            )
            json_content += f'    "target_fps": {config_data.get("target_fps", 240)},\n'
            json_content += "\n"
            json_content += "    // Master enable/disable switch\n"
            json_content += "    // true: Color Tracking Algo can be activated with start_key\n"
            json_content += "    // false: Color Tracking Algo completely disabled\n"
            json_content += f'    "enabled": {str(config_data.get("enabled", True)).lower()}\n'
            json_content += "}\n"

            # Write all content at once to avoid file handle issues
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(json_content)

            print(f"Configuration saved to {target_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def reset_to_defaults(self):
        """Resets all configuration to default values and saves."""
        for key, schema in self.DEFAULT_CONFIG.items():
            setattr(self, key, schema["default"])
        self.save()
        print("Configuration reset to defaults.")

    def ensure_profiles_dir(self):
        """Ensures the profiles directory exists."""
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)

    def get_profiles(self) -> list[str]:
        """Returns a list of available profile names."""
        self.ensure_profiles_dir()
        files = glob.glob(os.path.join(self.profiles_dir, "*.json"))
        # Return sorted list of filenames without extension
        return sorted([os.path.splitext(os.path.basename(f))[0] for f in files])

    def save_profile(self, name: str):
        """Saves current configuration as a named profile."""
        self.ensure_profiles_dir()
        # Sanitize name
        clean_name = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip()
        if not clean_name:
            raise ValueError("Invalid profile name")

        filepath = os.path.join(self.profiles_dir, f"{clean_name}.json")
        self.save(filepath=filepath)
        return clean_name

    def load_profile(self, name: str):
        """Loads a named profile into the current configuration."""
        self.ensure_profiles_dir()
        filepath = os.path.join(self.profiles_dir, f"{name}.json")
        if os.path.exists(filepath):
            self.load(filepath=filepath)
            # Auto-save to make it the active config
            self.save()
            return True
        return False

    def delete_profile(self, name: str):
        """Deletes a named profile."""
        self.ensure_profiles_dir()
        filepath = os.path.join(self.profiles_dir, f"{name}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def update(self, key: str, value: Any):
        """
        Update a configuration setting with validation and immediately save to config.json
        """
        if not hasattr(self, key):
            print(f"Unknown configuration key: {key}")
            return

        # Use centralized validation logic
        validated_value = self.validate(key, value)

        # Only update if value actually changed after validation
        old_value = getattr(self, key)
        if old_value == validated_value:
            return

        setattr(self, key, validated_value)
        print(f"Updated {key} to {validated_value}")

        # Debounce save operations
        current_time = time.time() * 1000
        if current_time - self._last_save_time >= self._save_debounce_ms:
            self.save()
            self._last_save_time = current_time
        else:
            self._schedule_save()

    def _schedule_save(self):
        """Schedule a delayed save operation with debouncing"""
        # Cancel any existing timer just in case
        if self._save_timer:
            self._save_timer.cancel()

        # Schedule save after debounce interval
        self._save_timer = threading.Timer(self._save_debounce_ms / 1000.0, self.save)
        self._save_timer.daemon = True  # Don't prevent app exit
        self._save_timer.start()

    def get_all(self) -> dict[str, Any]:
        """
        Get all configuration settings as a dictionary

        Returns:
            Dictionary of all configuration settings
        """
        config_dict = {}
        for key, value in self.__dict__.items():
            # Skip the config_file attribute
            if key != "config_file":
                config_dict[key] = value

        return config_dict
