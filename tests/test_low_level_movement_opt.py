from unittest.mock import MagicMock, patch

import pytest

from core.low_level_movement import LowLevelMovementSystem


class TestLowLevelMovementOptimization:
    def test_input_structure_reuse(self):
        """
        Verify that INPUT structures are reused between calls to avoid allocation overhead.
        This test expects the optimization to be implemented.
        """
        config = MagicMock()
        system = LowLevelMovementSystem(config, MagicMock())

        # Initialize the optimization (if not already done in __init__ by the time we run this)
        # But we are testing the class, so we assume we will modify __init__

        mock_user32 = MagicMock()
        mock_user32.SendInput.return_value = 1

        # Clear cached _send_input to force _get_user32 call (which we patch)
        system._send_input = None

        with patch.object(system, "_get_user32", return_value=mock_user32):
            # First call
            # First call
            system.move_mouse_relative(10, 20)

            if not mock_user32.SendInput.called:
                pytest.skip("SendInput not called - possibly due to platform restrictions or missing user32")

            args1 = mock_user32.SendInput.call_args[0]
            # args1[1] should be a byref to the INPUT structure
            # ctypes.byref returns an object with _obj attribute pointing to the actual structure
            obj1 = args1[1]._obj

            # Verify values
            assert obj1.type == 0  # INPUT_MOUSE
            assert obj1.ii.mi.dx == 10
            assert obj1.ii.mi.dy == 20

            # Second call
            system.move_mouse_relative(30, 40)
            args2 = mock_user32.SendInput.call_args[0]
            obj2 = args2[1]._obj

            # Verify values updated
            assert obj2.ii.mi.dx == 30
            assert obj2.ii.mi.dy == 40

            # CRITICAL: Verify object identity is the same (Reuse)
            assert obj1 is obj2, "INPUT structure was recreated instead of reused!"

    def test_absolute_movement_reuse(self):
        """Verify absolute movement also uses the cached structure."""
        config = MagicMock()
        system = LowLevelMovementSystem(config, MagicMock())

        mock_user32 = MagicMock()
        mock_user32.SendInput.return_value = 1

        # Clear cached _send_input to force _get_user32 call (which we patch)
        system._send_input = None

        with patch.object(system, "_get_user32", return_value=mock_user32):
            # First call
            system.move_mouse_absolute(100, 100)
            args1 = mock_user32.SendInput.call_args[0]
            obj1 = args1[1]._obj

            system.move_mouse_absolute(200, 200)
            args2 = mock_user32.SendInput.call_args[0]
            obj2 = args2[1]._obj

            assert obj1 is obj2, "INPUT structure was recreated in absolute movement!"
