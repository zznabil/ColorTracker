from unittest.mock import MagicMock, patch

import pytest

from core.capture import MSSBackend
from core.detection import DetectionSystem
from utils.config import Config


@pytest.fixture
def mock_config():
    config = Config()
    config.capture_method = "mss"
    return config


@pytest.fixture
def detection_system(mock_config):
    return DetectionSystem(mock_config, MagicMock())


def test_default_backend_is_mss(detection_system):
    """Verify default backend is MSS"""
    backend = detection_system._get_backend()
    assert isinstance(backend, MSSBackend)
    assert detection_system.config.capture_method == "mss"


def test_switch_to_dxgi_success(detection_system):
    """Verify switching config to 'dxgi' uses DXGIBackend"""
    detection_system.config.capture_method = "dxgi"

    with patch("core.detection.DXGIBackend") as MockDXGI:
        mock_instance = MockDXGI.return_value
        backend = detection_system._get_backend()

        assert backend == mock_instance
        assert detection_system._current_capture_method == "dxgi"
        MockDXGI.assert_called_once()


def test_fallback_to_mss_on_dxgi_failure(detection_system):
    """Verify fallback to MSS if DXGI initialization fails"""
    detection_system.config.capture_method = "dxgi"

    # Mock DXGIBackend to raise an exception on init
    with patch("core.detection.DXGIBackend", side_effect=ImportError("dxcam missing")):
        # Also ensure MSSBackend is available
        with patch("core.detection.MSSBackend") as MockMSS:
            backend = detection_system._get_backend()

            # Should receive MSS backend
            assert backend == MockMSS.return_value
            # Internal state should reflect fallback (either by updating config or just current method)
            # In my implementation, I updated self._current_capture_method to "mss"
            assert detection_system._current_capture_method == "mss"


def test_backend_cleanup_on_switch(detection_system):
    """Verify old backend is closed when switching"""
    # Start with MSS
    mss_backend = detection_system._get_backend()
    mss_backend.close = MagicMock()

    # Switch to DXGI
    detection_system.config.capture_method = "dxgi"
    with patch("core.detection.DXGIBackend"):
        detection_system._get_backend()

        # Verify MSS was closed
        mss_backend.close.assert_called()
