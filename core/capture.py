from abc import ABC, abstractmethod

import mss
import numpy as np
from numpy.typing import NDArray


class CaptureBackend(ABC):
    """
    Abstract base class for screen capture backends.
    """

    @abstractmethod
    def grab(self, region: dict) -> tuple[bool, NDArray[np.uint8] | None]:
        """
        Capture a screen region.

        Args:
            region: Dictionary with 'left', 'top', 'width', 'height' keys.

        Returns:
            Tuple containing (success, image_data).
            image_data should be a BGRA numpy array.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Cleanup resources.
        """
        pass


class MSSBackend(CaptureBackend):
    """
    MSS-based capture backend (Cross-platform, reliable).
    """

    def __init__(self):
        self._sct = mss.mss(with_cursor=False)

    def grab(self, region: dict) -> tuple[bool, NDArray[np.uint8] | None]:
        try:
            # MSS returns a raw bytes object, we convert to numpy
            # mss.grab returns BGRA by default
            sct_img = self._sct.grab(region)
            img_bgra = np.frombuffer(sct_img.bgra, dtype=np.uint8).reshape((sct_img.height, sct_img.width, 4))
            return True, img_bgra
        except Exception:
            return False, None

    def close(self) -> None:
        try:
            self._sct.close()
        except Exception:
            pass


class DXGIBackend(CaptureBackend):
    """
    DXGI-based capture backend using dxcam (Windows only, High Performance).
    """

    def __init__(self):
        # Initialize dxcam
        try:
            import dxcam
        except ImportError:
            raise ImportError("dxcam not installed") from None

        # output_color="BGRA" allows direct compatibility with existing pipeline
        self._camera = dxcam.create(output_color="BGRA", output_idx=0)
        # FORCE VSync OFF: This is critical. By default, Desktop Duplication API waits for VSync.
        # We use Grab Mode (video_mode=False) to avoid Full Screen Copy thread overhead and latency.
        # We manually manage caching to allow 1000Hz logic loop even if screen updates are slower.

        # We assume 1000Hz target, but we rely on manual grab() calls.
        # Video mode thread copies Full Screen 1440p -> 14MB per frame -> Bandwidth saturation (~120 FPS limit).
        # By using Grab Mode + Caching, we avoid blocking the logic loop.

        # Note: dxcam.start() is NOT called. We use direct grab().

        self.last_valid_frame = None

    def grab(self, region: dict) -> tuple[bool, NDArray[np.uint8] | None]:
        try:
            # dxcam uses (left, top, right, bottom)
            left = region["left"]
            top = region["top"]
            right = left + region["width"]
            bottom = top + region["height"]
            dxgi_region = (left, top, right, bottom)

            # Direct grab from dxcam (Non-blocking if no new frame usually, or fast return None)
            # dxcam.grab(region) handles the Copy/Map.
            # Issue: dxcam copies FULL screen then crops. This takes ~8ms on 1440p.
            # This caps "Fresh Data" FPS to ~125.
            # However, returning None is fast (0ms).

            frame = self._camera.grab(region=dxgi_region)

            if frame is None:
                # No new frame available (VSync or Timeout)
                # Return cached frame to keep logic loop spinning
                if self.last_valid_frame is not None:
                    # We must ensure the cached frame matches the requested region size/pos?
                    # If region changed, cached frame is invalid for this region.
                    # But DetectionSystem moves region.
                    # If we return old frame for NEW region, it's wrong.
                    # So we can only return cached frame if region matches?
                    # Actually, if region changes, we NEED new data.
                    # If we return None, DetectionSystem stops.
                    return False, None
                return False, None

            # Frame is valid
            self.last_valid_frame = frame
            return True, frame

        except Exception:
            return False, None

    def close(self) -> None:
        try:
            # No start/stop needed for grab mode
            del self._camera
        except Exception:
            pass
