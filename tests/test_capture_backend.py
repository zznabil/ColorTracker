import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from core.capture import MSSBackend, DXGIBackend
from core.detection import DetectionSystem
from utils.config import Config


# Mock mss to avoid actual screen capture during tests
@pytest.fixture
def mock_mss():
    with patch("mss.mss") as mock:
        instance = mock.return_value
        # Setup mock grab return
        mock_img = MagicMock()
        mock_img.bgra = b"\x00\x00\x00\xff" * 100 * 100  # 100x100 black image
        mock_img.width = 100
        mock_img.height = 100
        instance.grab.return_value = mock_img
        yield mock


# Mock dxcam
@pytest.fixture
def mock_dxcam():
    with patch("dxcam.create") as mock:
        camera = mock.return_value
        # Setup mock frame return
        camera.grab.return_value = np.zeros((100, 100, 4), dtype=np.uint8)  # BGRA
        camera.get_latest_frame.return_value = np.zeros((100, 100, 4), dtype=np.uint8)
        yield mock


@pytest.fixture
def detection_system():
    config = Config()
    config.screen_width = 1920
    config.screen_height = 1080
    config.capture_method = "mss"
    perf_monitor = MagicMock()
    return DetectionSystem(config, perf_monitor)


def test_mss_backend_initialization(mock_mss):
    backend = MSSBackend()
    assert backend is not None


def test_mss_backend_grab(mock_mss):
    backend = MSSBackend()
    region = {"left": 0, "top": 0, "width": 100, "height": 100}
    success, frame = backend.grab(region)
    assert success is True
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (100, 100, 4)


def test_detection_system_defaults_to_mss(detection_system, mock_mss):
    # Default config is "mss"
    # DetectionSystem uses lazy initialization for backend via _get_backend
    backend = detection_system._get_backend()
    assert isinstance(backend, MSSBackend)


def test_detection_system_switches_to_dxgi(detection_system, mock_dxcam):
    # Change config
    detection_system.config.capture_method = "dxgi"

    # Trigger backend update
    backend = detection_system._get_backend()
    assert isinstance(backend, DXGIBackend)


def test_dxgi_fallback_to_mss(detection_system):
    # Set to dxgi
    detection_system.config.capture_method = "dxgi"

    # Mock dxcam.create to raise ImportError or return None
    with patch("dxcam.create", side_effect=ImportError("dxcam not found")):
        backend = detection_system._get_backend()
        # Should fallback to MSS
        assert isinstance(backend, MSSBackend)


def test_dxgi_runtime_fallback(detection_system):
    # Set to dxgi
    detection_system.config.capture_method = "dxgi"

    # Mock dxcam.create to raise Exception
    with patch("dxcam.create", side_effect=Exception("DXGI Init Failed")):
        backend = detection_system._get_backend()
        assert isinstance(backend, MSSBackend)
