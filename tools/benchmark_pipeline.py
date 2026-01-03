import timeit

import cv2
import mss
import numpy as np


def benchmark_pipeline():
    print("Initializing Pipeline Benchmark...")
    print("Simulating: Grab -> FromBuffer -> Reshape -> InRange -> MinMaxLoc")

    with mss.mss(with_cursor=False) as sct:
        # Test case: Local Search (200x200)
        width = 200
        height = 200
        area = {"left": 0, "top": 0, "width": width, "height": height}

        # Pre-calculated bounds (simulating cached bounds)
        lower_bound = np.array([0, 0, 0, 0], dtype=np.uint8)
        upper_bound = np.array([50, 50, 50, 255], dtype=np.uint8)

        def pipeline_step():
            # 1. Grab
            sct_img = sct.grab(area)

            # 2. Convert (Zero-copy)
            img_bgra = np.frombuffer(sct_img.bgra, dtype=np.uint8).reshape((sct_img.height, sct_img.width, 4))

            # 3. Detection (Mask + Loc)
            mask = cv2.inRange(img_bgra, lower_bound, upper_bound)
            _, max_val, _, max_loc = cv2.minMaxLoc(mask)
            return max_loc

        # Warmup
        for _ in range(10):
            pipeline_step()

        # Benchmark
        iterations = 100
        total_time = timeit.timeit(pipeline_step, number=iterations)
        avg_time_s = total_time / iterations
        avg_time_ms = avg_time_s * 1000
        fps = 1.0 / avg_time_s if avg_time_s > 0 else 0

        print("\nResults (200x200 Region):")
        print(f"Total Time (100 frames): {total_time:.4f}s")
        print(f"Avg Frame Time:        {avg_time_ms:.2f} ms")
        print(f"Max Potential FPS:     {fps:.1f}")


if __name__ == "__main__":
    benchmark_pipeline()
