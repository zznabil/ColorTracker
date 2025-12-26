#!/usr/bin/env python3

"""
Configuration Utility

Handles loading and saving configuration settings, including profile management.
"""

import glob
import json
import os
import shutil
import threading
import time
from typing import Any


class Config:
    """Handles loading and saving configuration settings with self-healing capabilities and profile support"""

    # Type Hints for attributes
    screen_width: int
    screen_height: int
    target_color: int
    color_tolerance: int
    search_area: int
    fov_x: int
    fov_y: int
    smoothing: float
    filter_method: str
    aim_point: int
    head_offset: int
    leg_offset: int
    prediction_enabled: bool
    prediction_multiplier: float
    start_key: str
    stop_key: str
    target_fps: int
    enabled: bool
    debug_mode: bool
    config_file: str
    current_profile_name: str

    # Default configuration schema for validation and self-healing
    DEFAULT_CONFIG = {
        "screen_width": {"type": int, "default": 1920, "min": 640, "max": 7680},
        "screen_height": {"type": int, "default": 1080, "min": 480, "max": 4320},
        "target_color": {"type": int, "default": 0xC9008D},
        "color_tolerance": {"type": int, "default": 10, "min": 0, "max": 100},
        "search_area": {"type": int, "default": 100, "min": 10, "max": 1000},
        "fov_x": {"type": int, "default": 50, "min": 10, "max": 500},
        "fov_y": {"type": int, "default": 50, "min": 10, "max": 500},
        "smoothing": {"type": float, "default": 2.0, "min": 0.0, "max": 100.0},
        "filter_method": {
            "type": str,
            "default": "EMA",
            "options": ["EMA", "DEMA", "TEMA", "Median+EMA", "Dynamic EMA"],
        },
        "aim_point": {"type": int, "default": 1, "min": 0, "max": 2},
        "head_offset": {"type": int, "default": 20, "min": 0, "max": 200},
        "leg_offset": {"type": int, "default": 30, "min": 0, "max": 200},
        "prediction_enabled": {"type": bool, "default": True},
        "prediction_multiplier": {"type": float, "default": 0.5, "min": 0.0, "max": 100.0},
        "start_key": {"type": str, "default": "page_up"},
        "stop_key": {"type": str, "default": "page_down"},
        "target_fps": {"type": int, "default": 240, "min": 30, "max": 1000},
        "enabled": {"type": bool, "default": False},
        "debug_mode": {"type": bool, "default": False},
    }

    PROFILES_DIR = "profiles"
    DEFAULT_PROFILE_NAME = "default"

    def __init__(self):
        """
        Initialize configuration with default values
        """
        # Apply defaults from schema
        for key, schema in self.DEFAULT_CONFIG.items():
            setattr(self, key, schema["default"])

        # Internal state
        self.config_file = "config.json"
        self.current_profile_name = self.DEFAULT_PROFILE_NAME
        self._last_save_time = 0
        self._save_debounce_ms = 500
        self._save_timer = None
        self._lock = threading.Lock()

        # Ensure profiles directory exists
        if not os.path.exists(self.PROFILES_DIR):
            os.makedirs(self.PROFILES_DIR)

        # Initialize default profile if it doesn't exist but config.json does
        default_profile_path = os.path.join(self.PROFILES_DIR, f"{self.DEFAULT_PROFILE_NAME}.json")
        if not os.path.exists(default_profile_path) and os.path.exists("config.json"):
            try:
                shutil.copy("config.json", default_profile_path)
            except Exception as e:
                print(f"Config: Failed to migrate config.json to default profile: {e}")

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

    def load(self, profile_name: str | None = None):
        """
        Load configuration from file if it exists with robust validation and repair
        """
        # Determine the file path
        file_to_load = self.config_file

        if profile_name:
            # If explicit profile name provided, switch to it
            self.current_profile_name = profile_name
            file_to_load = os.path.join(self.PROFILES_DIR, f"{profile_name}.json")
            self.config_file = file_to_load
        else:
            # No profile name provided.
            # If config_file was manually set (e.g. by a test), use it.
            # But if config_file is currently pointing to a profile that isn't the one requested (none requested),
            # we should stick to self.config_file unless it's the initial load.

            # If self.config_file is just "config.json" (initial state), try to resolve to a profile
            if self.config_file == "config.json":
                default_profile_path = os.path.join(self.PROFILES_DIR, f"{self.DEFAULT_PROFILE_NAME}.json")
                if os.path.exists(default_profile_path):
                    file_to_load = default_profile_path
                    self.config_file = file_to_load
                else:
                     file_to_load = "config.json"
            else:
                # Use whatever is currently set
                file_to_load = self.config_file

        if not os.path.exists(file_to_load):
            print(f"Config: {file_to_load} not found. Using defaults.")
            # If loading a specific profile that doesn't exist, we might want to save defaults there
            if profile_name:
                self.save()
            return

        try:
            with open(file_to_load, encoding="utf-8") as f:
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
                    # Only print if we are actually loading a real file, not during tests usually
                    # print(f"Config Repair: Missing key '{key}' in {file_to_load}. Using default.")
                    setattr(self, key, self.DEFAULT_CONFIG[key]["default"])

            print(f"Configuration successfully loaded from {file_to_load}.")
        except Exception as e:
            print(f"Critical Error loading {file_to_load}: {e}. Falling back to safe defaults.")
            # Self-healing: Reset to defaults on critical failure
            for key, schema in self.DEFAULT_CONFIG.items():
                setattr(self, key, schema["default"])

    def save(self):
        """
        Save current configuration to file with detailed comments preserved
        """
        # Cancel any pending save timer since we are saving now
        if self._save_timer:
            self._save_timer.cancel()
            self._save_timer = None

        try:
            with self._lock:
                # Create a dictionary of all configuration attributes
                config_data = {}
                for key, value in self.__dict__.items():
                    # Skip internal attributes
                    if key not in [
                        "config_file",
                        "current_profile_name",
                        "_last_save_time",
                        "_save_debounce_ms",
                        "_save_timer",
                        "_lock",
                        "PROFILES_DIR",
                        "DEFAULT_PROFILE_NAME",
                        "DEFAULT_CONFIG",
                    ]:
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

            json_content += "    // === TRACKING BEHAVIOR SETTINGS ===\n"
            json_content += "    // Mouse movement smoothing (0.0 = instant, higher = smoother)\n"
            json_content += "    // 0.0-0.5: Very responsive (competitive gaming)\n"
            json_content += "    // 0.5-2.0: Balanced (general use)\n"
            json_content += "    // 2.0-10.0: Very smooth (casual gaming)\n"
            json_content += f'    "smoothing": {config_data.get("smoothing", 0.0)},\n'
            json_content += "\n"
            json_content += "    // Filtering method for prediction (Noise reduction)\n"
            json_content += '    // Options: "EMA", "DEMA", "TEMA", "Median+EMA", "Dynamic EMA"\n'
            json_content += f'    "filter_method": "{config_data.get("filter_method", "EMA")}",\n'
            json_content += "\n"
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

            json_content += "    // === PREDICTION SETTINGS ===\n"
            json_content += "    // Enable movement prediction for moving targets\n"
            json_content += "    // true: Predicts target movement (better for moving enemies)\n"
            json_content += "    // false: Tracks at current position (better for stationary targets)\n"
            json_content += f'    "prediction_enabled": {str(config_data.get("prediction_enabled", False)).lower()},\n'
            json_content += "\n"
            json_content += "    // Prediction strength multiplier (0.0-1.0)\n"
            json_content += "    // Higher values = more aggressive prediction\n"
            json_content += "    // Start with 0.1 and adjust based on game speed\n"
            json_content += f'    "prediction_multiplier": {config_data.get("prediction_multiplier", 0.1)},\n'
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
            with open(self.config_file, "w", encoding="utf-8") as f:
                f.write(json_content)

            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")

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

    def reset_to_defaults(self):
        """
        Reset all configuration settings to their default values and save immediately
        """
        print("Config: Resetting all settings to defaults...")
        for key, schema in self.DEFAULT_CONFIG.items():
            setattr(self, key, schema["default"])
        self.save()

    # === Profile Management ===

    def list_profiles(self) -> list[str]:
        """
        List all available profiles.

        Returns:
            List of profile names (without .json extension)
        """
        profiles = []
        if os.path.exists(self.PROFILES_DIR):
            for f in glob.glob(os.path.join(self.PROFILES_DIR, "*.json")):
                profiles.append(os.path.splitext(os.path.basename(f))[0])
        return sorted(profiles)

    def load_profile(self, profile_name: str) -> bool:
        """
        Switch to a different profile.

        Args:
            profile_name: Name of the profile to load

        Returns:
            True if successful, False otherwise
        """
        if not profile_name:
            return False

        path = os.path.join(self.PROFILES_DIR, f"{profile_name}.json")
        if not os.path.exists(path):
            print(f"Config: Profile '{profile_name}' does not exist.")
            return False

        # Force save current before switching? Maybe not, update() already saves.
        self.load(profile_name)
        return True

    def save_profile(self, profile_name: str) -> bool:
        """
        Save current settings as a new profile.

        Args:
            profile_name: Name for the new profile

        Returns:
            True if successful, False otherwise
        """
        if not profile_name:
            return False

        # Clean profile name (alphanumeric only recommended)
        clean_name = "".join(c for c in profile_name if c.isalnum() or c in ("-", "_"))
        if not clean_name:
            print("Config: Invalid profile name.")
            return False

        self.current_profile_name = clean_name
        self.config_file = os.path.join(self.PROFILES_DIR, f"{clean_name}.json")
        self.save()
        return True

    def delete_profile(self, profile_name: str) -> bool:
        """
        Delete a profile.

        Args:
            profile_name: Name of the profile to delete

        Returns:
            True if successful, False otherwise
        """
        if profile_name == self.DEFAULT_PROFILE_NAME:
            print("Config: Cannot delete default profile.")
            return False

        path = os.path.join(self.PROFILES_DIR, f"{profile_name}.json")
        if os.path.exists(path):
            try:
                os.remove(path)
                # If we deleted the current profile, switch to default
                if self.current_profile_name == profile_name:
                    self.load(self.DEFAULT_PROFILE_NAME)
                return True
            except Exception as e:
                print(f"Config: Error deleting profile: {e}")
                return False
        return False
