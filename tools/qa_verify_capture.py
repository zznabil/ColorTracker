import os
import sys
import time

sys.path.append(os.getcwd())

from core.detection import DetectionSystem
from utils.config import Config
from utils.performance_monitor import PerformanceMonitor


def verify():
    print("Initializing Verification...")
    config = Config()
    pm = PerformanceMonitor()

    # Force defaults
    config.fov_x = 100
    config.fov_y = 100
    config.target_color = 0xC9008D
    config.color_tolerance = 10

    # Test MSS
    print("\n--- Testing MSS Integration ---")
    config.capture_method = "mss"
    det = DetectionSystem(config, pm)
    try:
        start = time.time()
        frames = 0
        while time.time() - start < 2.0:
            det.find_target()
            frames += 1
        print(f"MSS Detection FPS: {frames / 2.0:.2f}")
    finally:
        det.close()

    # Test DXGI
    print("\n--- Testing DXGI Integration ---")
    config.capture_method = "dxgi"
    det = DetectionSystem(config, pm)
    try:
        start = time.time()
        frames = 0
        while time.time() - start < 2.0:
            det.find_target()
            frames += 1
        print(f"DXGI Detection FPS: {frames / 2.0:.2f}")
    finally:
        det.close()


if __name__ == "__main__":
    verify()
