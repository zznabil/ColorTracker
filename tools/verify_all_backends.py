import sys
import os
import time
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.detection import DetectionSystem
from utils.config import Config
from utils.performance_monitor import PerformanceMonitor
from utils.logger import Logger


def verify_backend(method_name):
    print(f"\n[-] Testing Backend: {method_name.upper()}...")

    # Setup Config
    config = Config()
    config.load()
    config.capture_method = method_name

    # Setup Monitor
    perf = PerformanceMonitor()

    # Init Detection
    try:
        detection = DetectionSystem(config, perf)

        # Verify Backend Type
        backend_cls = detection.backend.__class__.__name__
        print(f"[-] Initialized Class: {backend_cls}")

        expected_cls = {"mss": "MSSBackend", "dxgi": "DXGIBackend", "bettercam": "BetterCamBackend"}.get(method_name)

        if backend_cls == expected_cls:
            print(f"[+] SUCCESS: {method_name.upper()} backend loaded.")
        elif backend_cls == "MSSBackend":
            print(f"[!] FALLBACK: System reverted to MSS (Expected {expected_cls}).")
            if method_name != "mss":
                print("    (This is expected if dependencies are missing)")
        else:
            print(f"[?] UNEXPECTED: Got {backend_cls}")

        # Try a grab
        print("[-] Attempting frame grab...")
        t0 = time.perf_counter()
        found, x, y = detection.find_target()
        t1 = time.perf_counter()
        print(f"[-] Grab & Process Time: {(t1 - t0) * 1000:.2f}ms")

        detection.close()

    except Exception as e:
        print(f"[!] CRITICAL ERROR: {e}")


if __name__ == "__main__":
    # Test all known backends
    print("=== CAPTURE BACKEND VERIFICATION ===")

    # 1. MSS (Baseline)
    verify_backend("mss")

    # 2. DXGI (Hyper-Speed)
    verify_backend("dxgi")

    # 3. BetterCam (Ultra-Speed)
    verify_backend("bettercam")
    print("\n=== VERIFICATION COMPLETE ===")
