import timeit

import bettercam
import dxcam


def benchmark_dxgi():
    print("Initializing DXGI/GPU Capture Benchmark...")
    print("-" * 50)

    # 1. Benchmark DXCAM
    camera = None
    try:
        camera = dxcam.create()
        print("DXCAM initialized successfully.")

        def grab_dxcam():
            if camera:
                return camera.grab()

        # Warmup
        for _ in range(10):
            grab_dxcam()

        # Benchmark
        t = timeit.timeit(grab_dxcam, number=100)
        avg_ms = (t / 100) * 1000
        fps = 1000 / avg_ms if avg_ms > 0 else 0
        print(f"DXCAM Capture: {avg_ms:.2f} ms | {fps:.1f} FPS")
    except Exception as e:
        print(f"DXCAM Failed: {e}")
    finally:
        if camera:
            del camera

    print("-" * 50)

    # 2. Benchmark BETTERCAM
    camera = None
    try:
        camera = bettercam.create()
        print("BETTERCAM initialized successfully.")

        def grab_bettercam():
            if camera:
                return camera.grab()

        # Warmup
        for _ in range(10):
            grab_bettercam()

        # Benchmark
        t = timeit.timeit(grab_bettercam, number=100)
        avg_ms = (t / 100) * 1000
        fps = 1000 / avg_ms if avg_ms > 0 else 0
        print(f"BETTERCAM Capture: {avg_ms:.2f} ms | {fps:.1f} FPS")
    except Exception as e:
        print(f"BETTERCAM Failed: {e}")
    finally:
        if camera:
            del camera


if __name__ == "__main__":
    benchmark_dxgi()
