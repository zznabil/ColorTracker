import time
import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.capture import DXGIBackend


def verify_logic_decoupling():
    print("[-] Verifying Logic Loop Decoupling (Grab Mode Caching)...")

    try:
        # Initialize DXGI Backend (Grab Mode is default now in master)
        backend = DXGIBackend()
        print("[+] Backend initialized.")

        region = {"left": 960, "top": 540, "width": 200, "height": 200}

        # Warmup
        backend.grab(region)

        print("[-] Simulating 1000Hz Logic Loop (1000 iterations)...")

        start_time = time.perf_counter()

        iterations = 1000
        unique_frames = 0
        last_frame_data = None

        for i in range(iterations):
            # Simulate logic work (very fast)
            # time.sleep(0.0001)

            # Grab frame (should be non-blocking/cached)
            success, frame = backend.grab(region)

            if success:
                # Check uniqueness (simple bytes check for speed, might be slow if large)
                # Just check first pixel for speed
                current_data = frame[0, 0, 0]
                # Actually, if the scene is static, unique frames will be 0 based on content.
                # But we want to know if 'dxcam' returned a NEW object or the SAME object?
                # DXGIBackend creates new numpy array from buffer usually?
                # Or returns reference?
                # If cached, it returns `self.last_valid_frame`.
                # So `id(frame)` should be same if cached?

                if last_frame_data is None or id(frame) != id(last_frame_data):
                    unique_frames += 1
                    last_frame_data = frame

            # Smart sleep simulation (aiming for 1000 FPS total loop)
            # If grab takes 0ms, we sleep. If grab takes 8ms (new frame), we don't sleep.
            # We just measure raw throughput here.

        total_time = time.perf_counter() - start_time
        avg_logic_fps = iterations / total_time

        print("-" * 50)
        print(f"Total Time: {total_time:.4f}s")
        print(f"Logic Iterations: {iterations}")
        print(f"Logic FPS: {avg_logic_fps:.1f} (Target: >300)")
        print("-" * 50)

        if avg_logic_fps > 300:
            print("[+] SUCCESS: Logic loop is DECOUPLED from Capture rate.")
        else:
            print("[!] FAILURE: Logic loop is throttled by Capture.")

        backend.close()

    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    verify_logic_decoupling()
