import logging
import os
import sys
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.detection import DetectionSystem
from utils.config import Config
from utils.logger import Logger
from utils.performance_monitor import PerformanceMonitor


def verify_dxgi():
    print("[-] Initializing DXGI Verification...")

    # Setup Logger
    # logger = Logger(log_level=logging.DEBUG, log_to_file=False)
    # Just initialize it to ensure side effects (if any) or suppress it
    Logger(log_level=logging.DEBUG, log_to_file=False)

    # Setup Config
    config = Config()
    config.load()
    # Check capture_method attribute exists (it might be added dynamically or via update)
    current_method = getattr(config, "capture_method", "mss")
    print(f"[-] Config loaded. Capture Method: {current_method}")

    if current_method != "dxgi":
        print("[!] Warning: Config is not set to 'dxgi'. Overriding for test.")
        config.update("capture_method", "dxgi")

    # Setup Monitor
    perf = PerformanceMonitor()

    # Init Detection (this triggers backend creation)
    try:
        print("[-] Initializing DetectionSystem...")
        detection = DetectionSystem(config, perf)

        # Verify Backend Type (access protected member for verification)
        backend = detection._get_backend()
        backend_name = backend.__class__.__name__
        print(f"[-] Backend Initialized: {backend_name}")

        if backend_name == "DXGICaptureBackend":
            print("[+] SUCCESS: DXGI Backend active.")
        elif backend_name == "MSSCaptureBackend":
            print("[!] FAILURE: Fallback to MSS occurred. DXGI failed to init.")
        else:
            print(f"[?] Unknown backend: {backend_name}")

        # Try a grab
        print("[-] Attempting frame grab...")
        t0 = time.perf_counter()
        found, x, y = detection.find_target()
        t1 = time.perf_counter()
        print(f"[-] Grab & Process Time: {(t1 - t0) * 1000:.2f}ms")

        if found is not None:
            print("[+] Frame grab attempted successfully (Found/Not Found returned).")

        detection.close()

    except Exception as e:
        print(f"[!] CRITICAL ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    verify_dxgi()
