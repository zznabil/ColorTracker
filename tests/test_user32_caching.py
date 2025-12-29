from unittest.mock import MagicMock, patch

from core.low_level_movement import LowLevelMovementSystem


class TestUser32Caching:
    def test_user32_resolution_cached(self):
        """
        Verify that user32 is resolved once during initialization and reused.
        """
        config = MagicMock()

        # Setup a mock user32
        mock_user32 = MagicMock()
        mock_user32.SendInput.return_value = 1

        # We need to control the resolution process.
        # Since we are on Linux (likely), we need to ensure the resolution logic
        # hits our mock or behaves predictably.

        # We'll patch the internal resolution logic if possible, or just observe behavior.
        # A good way to test caching is to patch the mechanism that provides user32
        # and see if it's accessed only once.

        # In the current implementation (before opt), _get_user32 checks 'windll' every time.
        # We want to verify that in the new implementation, it doesn't.

        with patch('ctypes.windll', create=True) as mock_windll:
            mock_windll.user32 = mock_user32

            # This should trigger the resolution
            system = LowLevelMovementSystem(config)

            # Now we clear the source or change it to verify we are using the cached one
            mock_windll.user32 = None

            # If cached, this should still work (return the original mock)
            # Depending on how I implement it.
            # If I store the instance, changing the class/module attribute won't affect the instance attribute.

            # Access the cached attribute directly to verify it exists
            assert hasattr(system, "_user32"), "system should have _user32 attribute"
            assert system._user32 is mock_user32

            # And usage should use it
            # We can't easily test "usage uses it" without mocking the class internals
            # because the methods call _get_user32 (or self._user32 directly).

            # Let's verify that move_mouse_relative works using the cached instance
            # even if we "break" the global/module source.

            system.move_mouse_relative(10, 10)
            assert mock_user32.SendInput.called
