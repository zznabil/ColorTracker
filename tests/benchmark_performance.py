import os
import sys

sys.path.append(os.getcwd())

import time

from core.detection import DetectionSystem
from core.low_level_movement import LowLevelMovementSystem
from utils.config import Config


def benchmark():
    print("Initializing systems...")
    config = Config()
    # Ensure config has some reasonable defaults for testing
    config.enabled = True
    config.target_fps = 999
    config.screen_width = 1920
    config.screen_height = 1080

    detection = DetectionSystem(config)
    movement = LowLevelMovementSystem(config)

    # Warmup
    print("Warming up...")
    for _ in range(50):
        detection.find_target()
        movement.get_cursor_position()

    iterations = 100
    print(f"Running {iterations} iterations...")

    # Benchmark Detection
    start_time = time.perf_counter()
    for _ in range(iterations):
        detection.find_target()
    end_time = time.perf_counter()
    detection_time = (end_time - start_time) / iterations
    print(f"Detection Average Time: {detection_time * 1000:.4f} ms ({1 / detection_time:.1f} FPS)")

    # Benchmark Movement (Get Pos)
    start_time = time.perf_counter()
    for _ in range(iterations * 10):  # Run more times for movement since it's faster
        movement.get_cursor_position()
    end_time = time.perf_counter()
    movement_time = (end_time - start_time) / (iterations * 10)
    print(f"Movement (GetPos) Average Time: {movement_time * 1000:.4f} ms")

    # Benchmark Full Loop Simulation (without sleep)
    print("Simulating Full Loop...")
    start_time = time.perf_counter()
    for _ in range(iterations):
        found, x, y = detection.find_target()
        if found:
            movement.aim_at(x, y)
    end_time = time.perf_counter()
    loop_time = (end_time - start_time) / iterations
    print(f"Full Loop Average Time: {loop_time * 1000:.4f} ms ({1 / loop_time:.1f} FPS)")


if __name__ == "__main__":
    benchmark()
