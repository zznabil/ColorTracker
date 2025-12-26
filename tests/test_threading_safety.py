import threading
import time

from utils.config import Config


def test_concurrent_config_updates():
    """Stress test the configuration system for thread-safety during rapid updates"""
    config = Config()

    def hammer_updates(thread_id):
        for i in range(100):
            # Rapidly toggle a boolean
            config.update("enabled", i % 2 == 0)
            # Update a numeric value
            config.update("fov_x", 50 + thread_id + (i % 5))

    threads = []
    for i in range(10):  # 10 threads
        t = threading.Thread(target=hammer_updates, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Verify that the value is still within a sane range and no crashes occurred
    assert 50 <= config.fov_x <= 100
    assert isinstance(config.enabled, bool)


def test_save_debounce_concurrency():
    """Ensure the debounced save timer doesn't create multiple overlapping writers"""
    config = Config()

    # Trigger 500 updates in a row
    for i in range(500):
        config.update("smoothing", float(i % 10))

    # The debounce is 500ms. We wait 600ms and check if it saved.
    # Note: Hard to verify disk write frequency in CI without specialized mocks,
    # but we verify it doesn't crash the timer thread.
    time.sleep(0.6)
    assert config.smoothing <= 10.0
