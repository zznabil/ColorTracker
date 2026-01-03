import time
import timeit
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.motion_engine import MotionEngine
from utils.config import Config


def benchmark_motion():
    print("Initializing MotionEngine Benchmark...")

    # Setup
    config = Config()
    engine = MotionEngine(config)

    # Warmup JIT
    print("Warming up JIT...")
    for _ in range(100):
        engine.process(100, 100, 0.016)

    print("Running Benchmark (100,000 iterations)...")

    start_time = time.perf_counter()
    iterations = 100000

    # Simulate a target moving in a circle
    import math

    for i in range(iterations):
        t = i * 0.001
        x = 960 + 100 * math.cos(t)
        y = 540 + 100 * math.sin(t)
        engine.process(x, y, 0.001)

    total_time = time.perf_counter() - start_time
    avg_time_us = (total_time / iterations) * 1_000_000
    fps = iterations / total_time

    print("-" * 40)
    print(f"Total Time: {total_time:.4f}s")
    print(f"Avg Time per Call: {avg_time_us:.4f} µs")
    print(f"Throughput: {fps:,.0f} ops/sec")
    print("-" * 40)


if __name__ == "__main__":
    benchmark_motion()
