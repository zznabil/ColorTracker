from unittest.mock import MagicMock

import pytest

from core.low_level_movement import LowLevelMovementSystem


class TestLowLevelMovementOptimization:
    def test_input_structure_reuse(self):
        """
        Verify that INPUT structures are reused between calls to avoid allocation overhead.
        This test expects the optimization to be implemented.
        """
        config = MagicMock()
        system = LowLevelMovementSystem(config)

        mock_user32 = MagicMock()
        mock_user32.SendInput.return_value = 1

        # Inject mock directly as per optimization
        system._user32 = mock_user32

        # First call
        system.move_mouse_relative(10, 20)

        if not mock_user32.SendInput.called:
            pytest.fail("SendInput not called")

        # args1[1] should be a pointer to the INPUT structure
        # Since we cast to c_void_p in the code, we need to inspect the original object
        # or verify the pointer address if possible.
        # But wait, ctypes.cast returns a new object.

        # However, the code uses self._input_structure.
        # We can check if the fields in self._input_structure were updated correctly.

        # Verify values in the cached structure
        assert system._input_structure.type == 0  # INPUT_MOUSE
        assert system._input_structure.ii.mi.dx == 10
        assert system._input_structure.ii.mi.dy == 20

        # Capture the identity of the structure
        struct1 = system._input_structure

        # Second call
        system.move_mouse_relative(30, 40)

        # Verify values updated
        assert system._input_structure.ii.mi.dx == 30
        assert system._input_structure.ii.mi.dy == 40

        # CRITICAL: Verify object identity is the same (Reuse)
        assert system._input_structure is struct1, "INPUT structure was recreated instead of reused!"

    def test_absolute_movement_reuse(self):
        """Verify absolute movement also uses the cached structure."""
        config = MagicMock()
        system = LowLevelMovementSystem(config)

        mock_user32 = MagicMock()
        mock_user32.SendInput.return_value = 1

        # Inject mock directly
        system._user32 = mock_user32

        system.move_mouse_absolute(100, 100)
        struct1 = system._input_structure

        system.move_mouse_absolute(200, 200)
        struct2 = system._input_structure

        assert struct1 is struct2, "INPUT structure was recreated in absolute movement!"
