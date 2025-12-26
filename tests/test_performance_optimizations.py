#!/usr/bin/env python3

"""
Performance Optimization Tests for ColorTracker

Tests to verify that the performance optimizations achieve the target FPS.
"""

import os
import sys

sys.path.append(os.getcwd())

import time
from unittest.mock import Mock, patch

import numpy as np

from core.detection import DetectionSystem
from core.low_level_movement import LowLevelMovementSystem
from core.prediction import PredictionSystem
from utils.config import Config


def test_detection_performance():
    """Test detection system performance under optimized conditions"""
    print("Testing Detection System Performance...")

    config = Config()
    config.target_color = 0xFF0000  # Red
    config.color_tolerance = 10
    config.fov_x = 100
    config.fov_y = 100
    config.screen_width = 1920
    config.screen_height = 1080
    config.search_area = 50

    detection = DetectionSystem(config)

    # Mock MSS to avoid actual screen capture
    mock_sct = Mock()
    mock_sct.grab = Mock()

    # Create a mock image with a red pixel in the center
    test_width = 200
    test_height = 200
    mock_img = np.zeros((test_height, test_width, 4), dtype=np.uint8)
    mock_img[100, 100] = [0, 0, 255, 255]  # Red pixel in BGRA

    # Mock the screenshot object
    mock_screenshot = Mock()
    mock_screenshot.bgra = mock_img.tobytes()
    mock_sct.grab.return_value = mock_screenshot

    # Patch the thread-local MSS
    with patch.object(detection, "_get_sct", return_value=mock_sct):
        # Warmup
        for _ in range(10):
            detection.find_target()

        # Benchmark
        iterations = 100
        start_time = time.perf_counter()

        for _ in range(iterations):
            found, x, y = detection.find_target()

        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / iterations
        fps = 1.0 / avg_time

        print(f"  Detection: {fps:.1f} FPS ({avg_time * 1000:.2f}ms per frame)")

        # Should achieve at least 500 FPS for detection
        assert fps >= 500, f"Detection performance too low: {fps:.1f} FPS"

    return fps


def test_prediction_performance():
    """Test prediction system performance"""
    print("Testing Prediction System Performance...")

    config = Config()
    config.filter_method = "EMA"
    config.smoothing = 2.0
    config.prediction_enabled = True
    config.prediction_multiplier = 0.5

    prediction = PredictionSystem(config)

    # Warmup
    for i in range(10):
        prediction.predict(100 + i, 100 + i)

    # Benchmark
    iterations = 1000
    start_time = time.perf_counter()

    for i in range(iterations):
        prediction.predict(100 + i, 100 + i)

    end_time = time.perf_counter()
    avg_time = (end_time - start_time) / iterations
    fps = 1.0 / avg_time

    print(f"  Prediction: {fps:.1f} FPS ({avg_time * 1000:.3f}ms per frame)")

    # Should achieve at least 5000 FPS for prediction
    assert fps >= 5000, f"Prediction performance too low: {fps:.1f} FPS"

    return fps


def test_movement_performance():
    """Test movement system performance"""
    print("Testing Movement System Performance...")

    config = Config()
    config.screen_width = 1920
    config.screen_height = 1080

    movement = LowLevelMovementSystem(config)

    # Mock the actual mouse movement to avoid moving the cursor
    with patch("pyautogui.moveTo"):
        # Warmup
        for i in range(10):
            movement.aim_at(960 + i, 540 + i)

        # Benchmark
        iterations = 1000
        start_time = time.perf_counter()

        for i in range(iterations):
            movement.aim_at(960 + i, 540 + i)

        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / iterations
        fps = 1.0 / avg_time

        print(f"  Movement: {fps:.1f} FPS ({avg_time * 1000:.3f}ms per frame)")

        # Should achieve at least 2000 FPS for movement
        assert fps >= 2000, f"Movement performance too low: {fps:.1f} FPS"

    return fps


def test_full_pipeline_performance():
    """Test the complete pipeline performance"""
    print("Testing Full Pipeline Performance...")

    config = Config()
    config.target_color = 0xFF0000
    config.color_tolerance = 10
    config.fov_x = 100
    config.fov_y = 100
    config.screen_width = 1920
    config.screen_height = 1080
    config.search_area = 50
    config.filter_method = "EMA"
    config.smoothing = 2.0
    config.prediction_enabled = True
    config.prediction_multiplier = 0.5

    detection = DetectionSystem(config)
    prediction = PredictionSystem(config)
    movement = LowLevelMovementSystem(config)

    # Mock MSS
    mock_sct = Mock()
    test_width = 200
    test_height = 200
    mock_img = np.zeros((test_height, test_width, 4), dtype=np.uint8)
    mock_img[100, 100] = [0, 0, 255, 255]

    mock_screenshot = Mock()
    mock_screenshot.bgra = mock_img.tobytes()
    mock_sct.grab.return_value = mock_screenshot

    with patch.object(detection, "_get_sct", return_value=mock_sct):
        with patch("pyautogui.moveTo"):
            # Warmup
            for _i in range(20):
                found, x, y = detection.find_target()
                if found:
                    pred_x, pred_y = prediction.predict(x, y)
                    movement.aim_at(pred_x, pred_y)

            # Benchmark
            iterations = 100
            start_time = time.perf_counter()

            for _i in range(iterations):
                found, x, y = detection.find_target()
                if found:
                    pred_x, pred_y = prediction.predict(x, y)
                    movement.aim_at(pred_x, pred_y)

            end_time = time.perf_counter()
            avg_time = (end_time - start_time) / iterations
            fps = 1.0 / avg_time

            print(f"  Full Pipeline: {fps:.1f} FPS ({avg_time * 1000:.2f}ms per frame)")

            # Should achieve at least 240 FPS for full pipeline
            assert fps >= 240, f"Full pipeline performance too low: {fps:.1f} FPS"

    return fps


def test_high_fps_stability():
    """Test system stability at high FPS targets"""
    print("Testing High FPS Stability (960 FPS target)...")

    config = Config()
    config.target_color = 0xFF0000
    config.color_tolerance = 10
    config.fov_x = 100
    config.fov_y = 100
    config.screen_width = 1920
    config.screen_height = 1080
    config.search_area = 50
    config.filter_method = "EMA"
    config.smoothing = 2.0
    config.prediction_enabled = True
    config.prediction_multiplier = 0.5
    config.target_fps = 960

    detection = DetectionSystem(config)
    prediction = PredictionSystem(config)
    movement = LowLevelMovementSystem(config)

    # Mock MSS
    mock_sct = Mock()
    test_width = 200
    test_height = 200
    mock_img = np.zeros((test_height, test_width, 4), dtype=np.uint8)
    mock_img[100, 100] = [0, 0, 255, 255]

    mock_screenshot = Mock()
    mock_screenshot.bgra = mock_img.tobytes()
    mock_sct.grab.return_value = mock_screenshot

    with patch.object(detection, "_get_sct", return_value=mock_sct):
        with patch("pyautogui.moveTo"):
            # Simulate the algorithm loop with timing
            frame_interval = 1.0 / config.target_fps
            iterations = 500

            start_time = time.perf_counter()
            actual_frames = 0

            for _i in range(iterations):
                loop_start = time.perf_counter()

                # Run pipeline
                found, x, y = detection.find_target()
                if found:
                    pred_x, pred_y = prediction.predict(x, y)
                    movement.aim_at(pred_x, pred_y)

                actual_frames += 1

                # Simulate frame timing
                elapsed = time.perf_counter() - loop_start
                sleep_time = frame_interval - elapsed

                if sleep_time > 0:
                    time.sleep(sleep_time * 0.9)  # Sleep 90% of needed time
                    # Spin wait for remainder
                    target_time = loop_start + frame_interval
                    while time.perf_counter() < target_time:
                        pass

            end_time = time.perf_counter()
            actual_fps = actual_frames / (end_time - start_time)

            print(f"  High FPS Stability: {actual_fps:.1f} FPS achieved")

            # Should achieve at least 70% of target FPS (accounting for sleep overhead)
            min_fps = config.target_fps * 0.7
            assert actual_fps >= min_fps, f"Failed to achieve target FPS: {actual_fps:.1f} < {min_fps:.1f}"

    return actual_fps


if __name__ == "__main__":
    print("=" * 60)
    print("ColorTracker Performance Optimization Tests")
    print("=" * 60)

    try:
        det_fps = test_detection_performance()
        pred_fps = test_prediction_performance()
        move_fps = test_movement_performance()
        full_fps = test_full_pipeline_performance()
        stable_fps = test_high_fps_stability()

        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"Detection:     {det_fps:>8.1f} FPS")
        print(f"Prediction:    {pred_fps:>8.1f} FPS")
        print(f"Movement:      {move_fps:>8.1f} FPS")
        print(f"Full Pipeline: {full_fps:>8.1f} FPS")
        print(f"960 FPS Test:  {stable_fps:>8.1f} FPS")
        print("=" * 60)
        print("ALL PERFORMANCE TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
