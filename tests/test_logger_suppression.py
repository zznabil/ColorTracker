import logging
import time

import pytest

from utils.logger import Logger


class MockHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.count = 0
        self.messages = []

    def emit(self, record):
        self.count += 1
        self.messages.append(record.getMessage())


@pytest.fixture
def clean_logger():
    # Pass a specific instance or clear the singleton-ish logger
    logger_inst = Logger(log_level=logging.INFO, enable_debug_console=False)
    # Clear existing handlers to avoid double-logging from previous tests
    logger_inst.logger.handlers = []
    # Force clean state
    logger_inst.message_counts.clear()
    logger_inst.last_message_time.clear()
    logger_inst.suppressed_messages.clear()
    return logger_inst


def test_spam_suppression_logic(clean_logger):
    """Verify that the logger suppresses identical messages within a short window"""
    handler = MockHandler()
    clean_logger.logger.addHandler(handler)

    # Fire 20 identical logs in very fast succession
    for _ in range(20):
        clean_logger.info("Spammy pulse message")

    # With suppression, count should be exactly 1
    assert handler.count == 1


def test_suppression_expiration(clean_logger):
    """Verify that identical messages are allowed again after the cooldown period"""
    handler = MockHandler()
    clean_logger.logger.addHandler(handler)

    clean_logger.info("Unique message")
    # Same message again immediately (suppressed)
    clean_logger.info("Unique message")
    assert handler.count == 1

    # Wait for suppression to expire (cooldown is usually 1.0s)
    # But wait, looking at logger.py code:
    # It has self.spam_threshold = 5 (msgs/sec)
    # And "Less than spam threshold interval" logic: time_diff < (1.0 / self.spam_threshold) = 0.2s
    # So if we wait > 0.2s it should be fine?
    # Actually logic is: if time_diff < (1.0/5) -> Suppress.
    # So if time_diff >= 0.2s -> Allow.

    # Let's wait comfortably more than 0.2s
    time.sleep(1.0)

    clean_logger.info("Unique message")
    assert handler.count == 2


def test_hash_collision_resistance(clean_logger):
    """Ensure different messages are NOT suppressed"""
    handler = MockHandler()
    clean_logger.logger.addHandler(handler)

    clean_logger.info("Message A")
    clean_logger.info("Message B")

    assert handler.count == 2
