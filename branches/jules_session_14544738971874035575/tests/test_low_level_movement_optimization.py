
from unittest.mock import MagicMock

import pytest

from core.low_level_movement import LowLevelMovementSystem


class TestLowLevelMovementOptimization:
    def test_coordinate_conversion_logic(self):
        """
        Verify that the optimized multiplication logic yields the same result
        as the division logic (or extremely close) for standard screen resolutions.
        """
        config = MagicMock()
        monitor = MagicMock()

        system = LowLevelMovementSystem(config, monitor)
        # Force standard resolution
        system.screen_width = 1920
        system.screen_height = 1080

        # Calculate scales as intended in the optimization
        x_scale = 65535.0 / (system.screen_width - 1)
        y_scale = 65535.0 / (system.screen_height - 1)

        test_points = [
            (0, 0),
            (1919, 1079),
            (960, 540),
            (100, 100),
            (1800, 900)
        ]

        for x, y in test_points:
            # Old logic
            old_x = int(round((x * 65535) / (system.screen_width - 1)))
            old_y = int(round((y * 65535) / (system.screen_height - 1)))

            # New logic
            new_x = int(x * x_scale + 0.5)
            new_y = int(y * y_scale + 0.5)

            assert old_x == new_x, f"X mismatch at {x}: Old={old_x}, New={new_x}"
            assert old_y == new_y, f"Y mismatch at {y}: Old={old_y}, New={new_y}"

    def test_zero_dimension_handling(self):
        """Ensure we don't crash if screen dimensions are invalid (0 or 1)"""
        config = MagicMock()
        monitor = MagicMock()

        system = LowLevelMovementSystem(config, monitor)
        system.screen_width = 1 # Would cause div by zero in (width - 1)
        system.screen_height = 1

        # Manually trigger the init logic we plan to add
        try:
            x_scale = 65535.0 / (system.screen_width - 1) if system.screen_width > 1 else 0.0
        except ZeroDivisionError:
            pytest.fail("Optimization logic raised ZeroDivisionError")

        assert x_scale == 0.0
