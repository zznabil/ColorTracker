#!/usr/bin/env python3

"""
Configuration Utility

Handles loading and saving configuration settings.
OPTIMIZATIONS (V3.3.0 ULTRATHINK):
- Implements Observer Pattern via `__setattr__` override.
- Provides O(1) version integer for rapid change detection in hot loops.
- Atomic file I/O for robust persistence.
"""

import json
import os
import threading
import time
from typing import Any


class Config:
    """
    [Archetype A: The Sage - Logic/Data]
    Handles loading and saving configuration settings with self-healing capabilities
    """

    # Type Hints for attributes
    screen_width: int
    screen_height: int
    target_color: int
    color_tolerance: int
    # search_area removed per user request
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
    _version: int  # ULTRATHINK: Explicit type hint for version
    # Default configuration schema for validation and self-healing
    DEFAULT_CONFIG = {
        "screen_width": {"type": int, "default": 1920, "min": 640, "max": 7680},
        "screen_height": {"type": int, "default": 1080, "min": 480, "max": 4320},
        "target_color": {"type": int, "default": 0xC9008D},
        "color_tolerance": {"type": int, "default": 10, "min": 0, "max": 100},
        # "search_area": {"type": int, "default": 100, "min": 10, "max": 1000},
        "fov_x": {"type": int, "default": 50, "min": 5, "max": 500},
        "fov_y": {"type": int, "default": 50, "min": 5, "max": 500},
        "aim_point": {"type": int, "default": 1, "min": 0, "max": 2},
        "head_offset": {"type": int, "default": 20, "min": 0, "max": 200},
        "leg_offset": {"type": int, "default": 30, "min": 0, "max": 200},
        "motion_min_cutoff": {"type": float, "default": 0.5, "min": 0.01, "max": 25.0},
        "motion_beta": {"type": float, "default": 0.005, "min": 0.0001, "max": 0.3},
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
        # Initialize versioning (ULTRATHINK Optimization)
        # Use super().__setattr__ to bypass the overridden __setattr__ during init
        super().__setattr__("_version", 0)

        for key, schema in self.DEFAULT_CONFIG.items():
            setattr(self, key, schema["default"])

        # Internal state
        # USE ABSOLUTE PATH TO PREVENT SHADOWING IN DIFFERENT CWD
        from utils.paths import get_app_dir

        base_dir = get_app_dir()
        self.config_file = os.path.join(base_dir, "config.json")
        self._last_save_time = 0
        self._save_debounce_ms = 500
        self._save_timer = None
        self._lock = threading.Lock()

        # Load and validate saved configuration
        self.load()

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Overridden to provide O(1) change detection via versioning.
        (ULTRATHINK Optimization)
        """
        super().__setattr__(name, value)
        # Increment version only for actual config keys to invalidate caches
        # Check _version existence to avoid init issues
        if hasattr(self, "DEFAULT_CONFIG") and name in self.DEFAULT_CONFIG and hasattr(self, "_version"):
            # Direct modify to avoid recursion loop if _version was in DEFAULT_CONFIG (it's not)
            # We use super() to set _version to avoid re-triggering logic, though it's safe either way
            super().__setattr__("_version", self._version + 1)

    def validate(self, key: str, value: Any) -> Any:
        """
        Validates and repairs a specific configuration value using a declarative approach.
        """
        if key not in self.DEFAULT_CONFIG:
            return value

        schema = self.DEFAULT_CONFIG[key]
        expected_type = schema["type"]

        # 1. Type Correction with Guard Clauses
        try:
            if expected_type is bool:
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "y", "on")
                return bool(value)

            if expected_type is int and not isinstance(value, int):
                value = int(float(value))
            elif expected_type is float and not isinstance(value, float):
                value = float(value)
            elif expected_type is str and not isinstance(value, str):
                value = str(value)

        except (ValueError, TypeError):
            print(f"Config Repair: Invalid type for '{key}' (expected {expected_type.__name__}). Resetting to default.")
            return schema["default"]

        # 2. Range Validation (Clamping)
        if expected_type in (int, float):
            if "min" in schema:
                value = max(schema["min"], value)
            if "max" in schema:
                value = min(schema["max"], value)

        # 3. Option Validation
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

            if not content.strip():
                raise ValueError("Empty configuration file")

            # Strip comments
            import re

            content = re.sub(r"//.*", "", content)
            content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

            config_data = json.loads(content)

            # --- LEGACY KEY MAPPING ---
            # Smoothing (V2) -> Motion Min Cutoff & Motion Beta (V3)
            if "smoothing" in config_data:
                s = float(config_data["smoothing"])
                # Heuristic mapping: higher smoothing = lower cutoff and lower beta
                # Smoothing 50.0 is quite high for V3 defaults
                config_data["motion_min_cutoff"] = max(0.001, 0.05 / (s / 5.0 + 1.0))
                config_data["motion_beta"] = max(0.001, 0.05 / (s / 5.0 + 1.0))

            # Prediction Multiplier (V2/Dev) -> Prediction Scale (V3)
            if "prediction_multiplier" in config_data:
                config_data["prediction_scale"] = float(config_data["prediction_multiplier"])

            # Validate and apply each key from DEFAULT_SCHEMA
            updated_count = 0
            for key in self.DEFAULT_CONFIG.keys():
                if key in config_data:
                    value = config_data[key]
                    # Special handling for enum maps
                    if key == "aim_point" and isinstance(value, str):
                        aim_point_map = {"Head": 0, "Body": 1, "Legs": 2, "Chest": 1, "Center": 1}
                        value = aim_point_map.get(value, 1)

                    validated_value = self.validate(key, value)
                    setattr(self, key, validated_value)
                    updated_count += 1
                else:
                    # Missing key: load current value (which is default from __init__)
                    pass

            print(f"Configuration loaded and validated ({updated_count} keys applied from {self.config_file}).")
        except Exception as e:
            print(f"Critical Error loading {self.config_file}: {e}. Falling back to safe defaults.")
            # Self-healing: Reset to defaults on critical failure
            for key, schema in self.DEFAULT_CONFIG.items():
                setattr(self, key, schema["default"])

    def save(self):
        """
        Save current configuration to file using robust ATOMIC JSON serialization
        """
        if self._save_timer:
            self._save_timer.cancel()
            self._save_timer = None

        try:
            with self._lock:
                config_data = {}
                for key in self.DEFAULT_CONFIG.keys():
                    if hasattr(self, key):
                        config_data[key] = getattr(self, key)

                # ATOMIC SAVE: Write to temp file then rename
                temp_file = f"{self.config_file}.tmp"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=4, sort_keys=True)

                # Close file before replace (Windows requirement)
                os.replace(temp_file, self.config_file)

            print(f"Configuration saved ATOMICALLY to {self.config_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
            # Try to cleanup temp file if it exists
            temp_file = f"{self.config_file}.tmp"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

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
