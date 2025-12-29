import pytest
from unittest.mock import MagicMock, patch
from core.low_level_movement import LowLevelMovementSystem

class TestMovementEngines:
    def test_engine_switching(self):
        """Verify that LowLevelMovementSystem can switch between engines."""
        config = MagicMock()
        monitor = MagicMock()
        # Initial state should be 'standard'
        system = LowLevelMovementSystem(config, monitor)
        
        # We expect a way to set/get the engine
        assert hasattr(system, "set_engine")
        assert system.current_engine_name == "standard"
        
        # Mock a custom engine
        mock_engine = MagicMock()
        system.register_engine("test_engine", mock_engine)
        system.set_engine("test_engine")
        
        assert system.current_engine_name == "test_engine"
        
        # Verify call delegation
        system.move_mouse_relative(10, 20)
        mock_engine.move_relative.assert_called_once_with(10, 20)

    def test_standard_engine_delegation(self):
        """Verify that move calls are delegated to the engine implementation."""
        config = MagicMock()
        monitor = MagicMock()
        system = LowLevelMovementSystem(config, monitor)
        
        # Mock the engine instance
        mock_engine = MagicMock()
        system._engines["standard"] = mock_engine
        
        system.move_mouse_relative(5, 5)
        mock_engine.move_relative.assert_called_once_with(5, 5)
        
        system.move_mouse_absolute(100, 100)
        mock_engine.move_absolute.assert_called_once_with(100, 100)

    def test_fallback_on_engine_failure(self):
        """Verify that system falls back to standard engine if stealth engine fails."""
        config = MagicMock()
        monitor = MagicMock()
        system = LowLevelMovementSystem(config, monitor)
        
        standard_mock = MagicMock()
        stealth_mock = MagicMock()
        stealth_mock.move_relative.side_effect = Exception("Stealth failure")
        
        system.register_engine("stealth", stealth_mock)
        system.register_engine("standard", standard_mock)
        
        system.set_engine("stealth")
        
        # Should call stealth, catch exception, log warning, and fall back
        system.move_mouse_relative(10, 10)
        
        assert stealth_mock.move_relative.called
        assert system.current_engine_name == "standard"
        standard_mock.move_relative.assert_called_once_with(10, 10)
