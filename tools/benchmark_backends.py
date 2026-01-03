import os
import sys
import timeit

# Ensure project root is in path
sys.path.append(os.getcwd())

from core.capture import DXGIBackend, MSSBackend


def benchmark():
    # Use a standard 1080p region or smaller if 1920x1080 is too big for test env
    # But real use case is often small region. Let's test both?
    # The user requirement mentions > 300 FPS.
    # MSS is usually ~70-150 FPS full screen, but faster for small regions.
    # DXGI should be fast for full screen too.

    # 1. Full Screen Benchmark
    region_full = {"left": 0, "top": 0, "width": 1920, "height": 1080}

    # 2. FOV Benchmark (typical use case)
    region_fov = {"left": 960 - 100, "top": 540 - 100, "width": 200, "height": 200}

    print("=== MSSBackend Benchmark ===")
    mss = MSSBackend()
    try:
        # Full Screen
        def run_mss_full():
            mss.grab(region_full)

        t = timeit.timeit(run_mss_full, number=50)
        print(f"MSS Full Screen (1080p): {50 / t:.2f} FPS")

        # FOV
        def run_mss_fov():
            mss.grab(region_fov)

        t = timeit.timeit(run_mss_fov, number=200)
        print(f"MSS FOV (200x200):     {200 / t:.2f} FPS")

    finally:
        mss.close()

    print("\n=== DXGIBackend Benchmark ===")
    try:
        dxgi = DXGIBackend()

        # Full Screen
        def run_dxgi_full():
            dxgi.grab(region_full)

        # Warmup
        for _ in range(10):
            dxgi.grab(region_full)

        t = timeit.timeit(run_dxgi_full, number=200)
        print(f"DXGI Full Screen (1080p): {200 / t:.2f} FPS")

        # FOV
        def run_dxgi_fov():
            dxgi.grab(region_fov)

        t = timeit.timeit(run_dxgi_fov, number=500)
        print(f"DXGI FOV (200x200):     {500 / t:.2f} FPS")

        dxgi.close()
    except Exception as e:
        print(f"DXGI failed: {e}")


if __name__ == "__main__":
    benchmark()
