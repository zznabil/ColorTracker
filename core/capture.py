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
        self._camera.start(target_fps=1000, video_mode=True)  # Start in video mode for buffering
        # Wait a bit for initialization? usually start returns immediately.
        # Video mode is faster as it keeps a buffer.

    def grab(self, region: dict) -> tuple[bool, NDArray[np.uint8] | None]:
        try:
            # dxcam uses (left, top, right, bottom)
            left = region["left"]
            top = region["top"]
            right = left + region["width"]
            bottom = top + region["height"]

            # get_latest_frame() returns the last captured frame from the buffer
            # This is non-blocking and extremely fast
            frame = self._camera.get_latest_frame()

            if frame is None:
                return False, None

            # Crop to region
            # Frame is [height, width, channels]
            # Since we are capturing full screen in video mode usually?
            # dxcam with start() captures full screen. We need to crop.
            # OR we can configure start(region=...).
            # But if region changes (FOV changes), we'd need to restart.
            # DetectionSystem changes region dynamicall for local search vs full search.
            # So capturing full screen and cropping is safer for dynamic regions,
            # though less efficient than capturing only ROI if ROI was static.
            # Given the high speed of DXGI, cropping numpy array is fast.

            # Wait, dxcam's get_latest_frame returns the full screen image if start() was called without region.
            # Let's check how expensive cropping is. It's just slicing.

            roi = frame[top:bottom, left:right]

            # Check if we need to ensure contiguous array?
            # cv2 sometimes prefers it, but numpy slicing usually works.

            return True, roi

        except Exception:
            return False, None

    def close(self) -> None:
        try:
            self._camera.stop()
            del self._camera
        except Exception:
            pass
