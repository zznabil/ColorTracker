from unittest.mock import MagicMock, patch
import pytest
from core.low_level_movement import LowLevelMovementSystem, StandardEngine

class TestLowLevelMovementOptimization:
    def test_input_structure_reuse(self):
        """
        Verify that INPUT structures are reused in StandardEngine to avoid allocation overhead.
        """
        # Test StandardEngine directly for reuse optimization
        engine = StandardEngine(1920, 1080)
        
        mock_send = MagicMock(return_value=1)
        engine._send_input = mock_send

        # First call
        engine.move_relative(10, 20)
        args1 = mock_send.call_args[0]
        obj1 = args1[1]._obj

        # Second call
        engine.move_relative(30, 40)
        args2 = mock_send.call_args[0]
        obj2 = args2[1]._obj

        # CRITICAL: Verify object identity is the same (Reuse)
        assert obj1 is obj2, "INPUT structure was recreated instead of reused in StandardEngine!"

    def test_absolute_movement_reuse(self):
        """Verify absolute movement also uses the cached structure in StandardEngine."""
        engine = StandardEngine(1920, 1080)
        
        mock_send = MagicMock(return_value=1)
        engine._send_input = mock_send

        engine.move_absolute(100, 100)
        args1 = mock_send.call_args[0]
        obj1 = args1[1]._obj

        engine.move_absolute(200, 200)
        args2 = mock_send.call_args[0]
        obj2 = args2[1]._obj

        assert obj1 is obj2, "INPUT structure was recreated in absolute movement!"

    def test_system_delegation_and_fallback(self):
        """Verify LowLevelMovementSystem correctly delegates and handles failures."""
        config = MagicMock()
        monitor = MagicMock()
        system = LowLevelMovementSystem(config, monitor)
        
        # Mock engines
        standard_mock = MagicMock()
        stealth_mock = MagicMock()
        
        system.register_engine("standard", standard_mock)
        system.register_engine("stealth", stealth_mock)
        
        # Test standard delegation
        system.set_engine("standard")
        system.move_mouse_relative(1, 1)
        standard_mock.move_relative.assert_called_once()
        
        # Test stealth delegation
        system.set_engine("stealth")
        system.move_mouse_relative(2, 2)
        stealth_mock.move_relative.assert_called_once()