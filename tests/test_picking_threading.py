from unittest.mock import MagicMock, patch

import pytest

# We need to mock dpg BEFORE main is imported in some contexts,
# but here it's already imported. So we patch where it's used.


class TestPickingThreading:
    """Test threading safety of the picking mode"""

    @pytest.fixture
    def app(self):
        # Mock ALL of dearpygui.dearpygui
        mock_dpg = MagicMock()

        # Setup context managers
        mock_dpg.theme.return_value.__enter__.return_value = MagicMock()
        mock_dpg.window.return_value.__enter__.return_value = MagicMock()
        mock_dpg.group.return_value.__enter__.return_value = MagicMock()
        mock_dpg.tooltip.return_value.__enter__.return_value = MagicMock()
        mock_dpg.tab_bar.return_value.__enter__.return_value = MagicMock()
        mock_dpg.tab.return_value.__enter__.return_value = MagicMock()
        mock_dpg.collapsing_header.return_value.__enter__.return_value = MagicMock()

        # Mock other returns
        mock_dpg.does_item_exist.return_value = True
        mock_dpg.get_viewport_width.return_value = 1920
        mock_dpg.get_viewport_height.return_value = 1080

        with (
            patch("main.dpg", mock_dpg),
            patch("gui.main_window.dpg", mock_dpg),
            patch("main.Logger"),
            patch("main.Config"),
        ):
            from main import ColorTrackerAlgo

            app = ColorTrackerAlgo()
            # Manually inject mocks that might have been lost during init
            app.logger = MagicMock()
            app.config = MagicMock()
            app.config.enabled = False
            app.config.start_key = "pageup"
            app.config.stop_key = "pagedown"
            app.config.target_fps = 60

            return app

    def test_start_picking_mode_does_not_init_mss(self, app):
        """Verify start_picking_mode does not initialize MSS"""
        app.start_picking_mode()
        assert app.picking_mode is True
        assert app._picking_sct is None

    @patch("mss.mss")
    @patch("ctypes.windll.user32.GetAsyncKeyState", return_value=0)
    @patch("ctypes.windll.user32.GetCursorPos")
    def test_update_picking_logic_inits_mss(self, mock_get_pos, mock_get_async, mock_mss, app):
        """Verify update_picking_logic initializes MSS lazily"""
        app.picking_mode = True
        app._picking_sct = None

        app._update_picking_logic()

        mock_mss.assert_called_once()
        assert app._picking_sct is not None

    def test_exit_picking_mode_cleans_up(self, app):
        """Verify exit_picking_mode cleans up resources"""
        mock_sct = MagicMock()
        app.picking_mode = True
        app._picking_sct = mock_sct

        app._exit_picking_mode(cancelled=True)

        assert app.picking_mode is False
        assert app._picking_sct is None
        mock_sct.close.assert_called_once()

    def test_exit_picking_mode_handles_none_sct(self, app):
        """Verify exit_picking_mode handles None sct gracefully"""
        app.picking_mode = True
        app._picking_sct = None

        # Should not raise exception
        app._exit_picking_mode(cancelled=True)
        assert app.picking_mode is False
