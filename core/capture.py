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
    Uses 'Grab Mode' (Manual) with caching to bypass VSync locking.
    """

    def __init__(self):
        try:
            import dxcam
        except ImportError:
            raise ImportError("dxcam not installed") from None

        # output_color="BGRA" allows direct compatibility with existing pipeline
        self._camera = dxcam.create(output_color="BGRA", output_idx=0)
        self.last_valid_frame = None

    def grab(self, region: dict) -> tuple[bool, NDArray[np.uint8] | None]:
        try:
            # dxcam uses (left, top, right, bottom)
            left = region["left"]
            top = region["top"]
            right = left + region["width"]
            bottom = top + region["height"]
            dxgi_region = (left, top, right, bottom)

            # Direct grab from dxcam
            frame = self._camera.grab(region=dxgi_region)

            if frame is None:
                # No new frame available (VSync limit)
                # Return cached frame to allow Logic Loop to spin at 1000Hz+
                if self.last_valid_frame is not None:
                    return True, self.last_valid_frame
                return False, None

            self.last_valid_frame = frame
            return True, frame

        except Exception:
            return False, None

    def close(self) -> None:
        try:
            del self._camera
        except Exception:
            pass


class BetterCamBackend(CaptureBackend):
    """
    BetterCam-based capture backend (High Performance, Region Optimized).
    Supports very fast region capture (~400 FPS visual) via NVIDIA NvFBC or Desktop Duplication.
    """

    def __init__(self):
        try:
            import bettercam
        except ImportError:
            raise ImportError("bettercam not installed") from None

        # Output 0, BGRA color mode
        self._camera = bettercam.create(output_idx=0, output_color="BGRA")
        self.last_valid_frame = None

    def grab(self, region: dict) -> tuple[bool, NDArray[np.uint8] | None]:
        try:
            # bettercam expects (left, top, right, bottom)
            left = region["left"]
            top = region["top"]
            right = left + region["width"]
            bottom = top + region["height"]

            # Direct region grab
            frame = self._camera.grab(region=(left, top, right, bottom))

            if frame is None:
                # Fallback to cache if capture fails
                # Return cached frame to allow Logic Loop to spin at 1000Hz+
                if self.last_valid_frame is not None:
                    return True, self.last_valid_frame
                return False, None

            self.last_valid_frame = frame
            return True, frame

        except Exception:
            return False, None

    def close(self) -> None:
        try:
            del self._camera
        except Exception:
            pass
