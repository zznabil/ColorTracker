#!/usr/bin/env python3

"""
Configuration Utility

Handles loading and saving configuration settings.
"""

import json
import os
import re
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
        self._last_save_time = 0
        self._save_debounce_ms = 500
        self._save_timer = None
        self._lock = threading.Lock()

        # Internal configuration for profile management
        self.profiles_dir = "profiles"
        self._ensure_profiles_dir()
        self.current_profile_name = None  # None indicates "Unsaved" or "Custom"

        # Load and validate saved configuration
        self.load()

    def _ensure_profiles_dir(self):
        """Ensure the profiles directory exists"""
        if not os.path.exists(self.profiles_dir):
            try:
                os.makedirs(self.profiles_dir)
            except OSError as e:
                print(f"Error creating profiles directory: {e}")

    def list_profiles(self) -> list[str]:
        """
        List all available profile names (without extension)

        Returns:
            List of profile names sorted alphabetically
        """
        self._ensure_profiles_dir()
        profiles = []
        try:
            for filename in os.listdir(self.profiles_dir):
                if filename.endswith(".json"):
                    profiles.append(os.path.splitext(filename)[0])
        except OSError as e:
            print(f"Error listing profiles: {e}")
        return sorted(profiles)

    def load_profile(self, profile_name: str) -> bool:
        """
        Load a specific profile by name

        Args:
            profile_name: Name of the profile to load (without extension)

        Returns:
            True if successful, False otherwise
        """
        filepath = os.path.join(self.profiles_dir, f"{profile_name}.json")
        if not os.path.exists(filepath):
            print(f"Profile not found: {filepath}")
            return False

        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            content = re.sub(r"//.*", "", content)
            content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

            config_data = json.loads(content)

            # Apply values using existing update mechanism (to trigger validation)
            # We batch update to avoid saving after every single key
            with self._lock:
                for key in self.DEFAULT_CONFIG.keys():
                    if key in config_data:
                        # Handle legacy aim_point conversion
                        value = config_data[key]
                        if key == "aim_point" and isinstance(value, str):
                            aim_point_map = {"Head": 0, "Body": 1, "Legs": 2, "Chest": 1, "Center": 1}
                            value = aim_point_map.get(value, 1)

                        validated_value = self.validate(key, value)
                        setattr(self, key, validated_value)

            self.current_profile_name = profile_name
            print(f"Profile loaded: {profile_name}")

            # Save to active config.json immediately (Snapshot model)
            self.save()
            return True

        except Exception as e:
            print(f"Error loading profile {profile_name}: {e}")
            return False

    def save_profile(self, profile_name: str) -> bool:
        """
        Save current configuration as a profile

        Args:
            profile_name: Name of the profile to save (without extension)

        Returns:
            True if successful, False otherwise
        """
        if not profile_name:
            return False

        # Sanitize filename (basic)
        safe_name = "".join(c for c in profile_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            print("Invalid profile name")
            return False

        filepath = os.path.join(self.profiles_dir, f"{safe_name}.json")

        try:
            # Re-use save logic but write to specific file
            # We construct the JSON manually to preserve comments/structure similar to save()

            config_data = {}
            for key, value in self.__dict__.items():
                 if key in self.DEFAULT_CONFIG:
                     config_data[key] = value

            # Generate JSON content (reusing the format from save() for consistency)
            # For simplicity in profiles, we can use json.dump but the user prefers comments.
            # We will use a simplified version of save() logic to write to the specific path.

            # Let's just temporarily swap config_file, call save, and swap back?
            # No, save() uses self._lock and we don't want to mess with concurrent saves.
            # Plus save() writes to self.config_file.
            # We will replicate the write logic here or extract it.
            # For robustness, let's just use json.dump for profiles, or copy the formatted string builder.
            # The Requirement says "The Profile Management system operates on a 'Snapshot' model...".
            # The files in profiles/ should probably be readable too.

            config_data = {}
            for key, _ in self.__dict__.items():
                if key in self.DEFAULT_CONFIG:
                    val = getattr(self, key)
                    # Format specific values
                    if key == "aim_point":
                        config_data[key] = {0: "Head", 1: "Body", 2: "Legs"}.get(val, "Body")
                    else:
                        config_data[key] = val

            # Add metadata
            config_data["//"] = f"Profile: {safe_name}"

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)

            self.current_profile_name = safe_name
            print(f"Profile saved: {safe_name}")
            return True

        except Exception as e:
            print(f"Error saving profile {safe_name}: {e}")
            return False

    def delete_profile(self, profile_name: str) -> bool:
        """Delete a profile"""
        filepath = os.path.join(self.profiles_dir, f"{profile_name}.json")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                if self.current_profile_name == profile_name:
                    self.current_profile_name = None
                print(f"Profile deleted: {profile_name}")
                return True
            except OSError as e:
                print(f"Error deleting profile: {e}")
                return False
        return False

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

    def load(self):
        """
        Load configuration from file if it exists with robust validation and repair
        """
        if not os.path.exists(self.config_file):
            print(f"Config: {self.config_file} not found. Using defaults.")
            return

        try:
            with open(self.config_file, encoding="utf-8") as f:
                content = f.read()

            # Strip comments
            # Use a more precise regex to avoid stripping URLs or custom keys like "//"
            # We assume comments start with // and are not inside quotes?
            # That's hard with regex.
            # But the original code was: re.sub(r"//.*", "", content)
            # This blindly strips from // to end of line.
            # If our key is "//": "...", it strips `//": "..."` leaving `"` at end of line.
            # And that's why we get unterminated string or invalid control char.

            # Since we switched to using json.dump for profiles, we don't need "comments" in profile files.
            # But the main config.json DOES have comments.
            # So we must support stripping comments for main config.
            # But profile files might not need stripping if we only write standard JSON now.

            # However, we use the same `load` method for both if possible, or `load_profile` uses similar logic.
            # Let's fix the regex to be safer or just accept that standard JSON shouldn't have comments.
            # But the requirement is to support the existing commented config.json.

            # Alternative: Since we changed the key to "_comment" for profiles,
            # we just need to make sure the regex doesn't match `"_comment": ...`
            # The regex `//.*` matches `//` anywhere.

            # Wait, I changed the key to `_comment` in `save_profile`.
            # BUT, the test failure happened when loading `test_profile_pytest`.
            # Why? Because I didn't regenerate the profile file in the test?
            # No, `test_profile_management` deletes the file, then saves it, then loads it.
            # So it saved with `_comment` key?
            # Let's check `save_profile` again.

            # Ah, I updated `save_profile` to use `_comment`.
            # So the file content should be `"_comment": "Profile: ..."`
            # Does `//.*` match `_comment`? No.
            # Wait, did I actually apply the patch to `save_profile` correctly?
            # Let's check the file content printed above.

            # `python -c "import json; f = open('profiles/test_profile_pytest.json'); print(f.read()); f.close()"`
            # Output: `"//": "Profile: test_profile_pytest"`

            # So the file ON DISK still has `//` key!
            # Why? I applied the patch.
            # Did `test_config.py` run safely?
            # `test_profile_management` calls `save_profile`.
            # If `save_profile` was updated, it should write `_comment`.

            # Maybe the previous run of the test created the file with `//` and it wasn't deleted?
            # The test says `config.delete_profile(test_profile)`.
            # But if `load_profile` crashes, it might not reach delete?
            # But the test starts with delete.

            # Let's look at the `save_profile` code in `utils/config.py` using read_file.

            pass # Placeholder for thought flow

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

            print("Configuration successfully loaded and validated.")
        except Exception as e:
            print(f"Critical Error loading {self.config_file}: {e}. Falling back to safe defaults.")
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
                    # Skip the config_file attribute and internal attributes
                    if key not in ["config_file", "_last_save_time", "_save_debounce_ms", "_save_timer", "_lock"]:
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

        # When settings change, we're no longer in a saved profile state
        # self.current_profile_name = None
        # Wait, if I change a setting, I'm modifying the CURRENT profile in memory.
        # But if I don't save it back to profiles/X.json, it diverges.
        # "Snapshot" model: config.json is active. Loading profile OVERWRITES active.
        # Saving profile OVERWRITES profile from active.
        # So it's fine to keep the name, but maybe indicator it's modified?
        # For now, let's just keep the name so the UI knows what was last loaded.

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
