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
    # In FastLogger it's self.suppression_window = 1.0
    time.sleep(1.5)  # Be generous with timing

    clean_logger.info("Unique message")
    assert handler.count == 2


def test_hash_collision_resistance(clean_logger):
    """Ensure different messages are NOT suppressed"""
    handler = MockHandler()
    clean_logger.logger.addHandler(handler)

    clean_logger.info("Message A")
    clean_logger.info("Message B")

    assert handler.count == 2
