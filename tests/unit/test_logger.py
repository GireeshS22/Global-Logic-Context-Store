"""
Unit tests for logger utility.

Tests cover:
- Logger initialization
- Getting logger instances
- Log level configuration
- Logger reset functionality

Author: PhD Project
Version: 0.1.0
"""

import pytest
import logging
from logging.handlers import RotatingFileHandler
import tempfile
from pathlib import Path

from glcs.utils.logger import setup_logging, get_logger, reset_logging


def test_setup_logging():
    """Test setting up logging from config file."""
    # Reset first to ensure clean state
    reset_logging()

    # Setup with actual config file
    setup_logging("config/logging.yaml")

    # Get a logger and verify it's configured
    logger = get_logger("test_logger")
    assert logger is not None
    assert isinstance(logger, logging.Logger)


def test_get_logger_default():
    """Test getting a logger with default configuration."""
    reset_logging()

    logger = get_logger("test.module")

    assert logger is not None
    assert logger.name == "test.module"
    assert isinstance(logger, logging.Logger)


def test_get_logger_with_level_override():
    """Test getting a logger with level override."""
    reset_logging()

    # Get logger with DEBUG level
    logger = get_logger("test.debug", level="DEBUG")

    assert logger.level == logging.DEBUG


def test_get_logger_multiple_instances():
    """Test getting multiple logger instances."""
    reset_logging()

    logger1 = get_logger("module1")
    logger2 = get_logger("module2")
    logger3 = get_logger("module1")  # Same name as logger1

    # Different names should be different loggers
    assert logger1 is not logger2

    # Same name should return same logger instance
    assert logger1 is logger3


def test_logger_levels():
    """Test different log levels work correctly."""
    reset_logging()

    logger = get_logger("test.levels")

    # These should not raise exceptions
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")


def test_reset_logging():
    """Test resetting logging configuration."""
    # Setup logging
    setup_logging("config/logging.yaml")
    logger1 = get_logger("test.before_reset")

    # Reset
    reset_logging()

    # Get new logger after reset
    logger2 = get_logger("test.after_reset")

    # Logger should still work
    assert logger2 is not None
    logger2.info("Test message after reset")


def test_get_logger_auto_configures():
    """Test that get_logger auto-configures if logging not set up."""
    reset_logging()

    # Get logger without explicit setup
    logger = get_logger("test.auto")

    # Should auto-configure and work
    assert logger is not None
    logger.info("Auto-configured logging works")


def test_logger_name_hierarchy():
    """Test logger name hierarchy works correctly."""
    reset_logging()

    parent_logger = get_logger("glcs")
    child_logger = get_logger("glcs.core")
    grandchild_logger = get_logger("glcs.core.memory")

    # All should be valid loggers
    assert parent_logger is not None
    assert child_logger is not None
    assert grandchild_logger is not None

    # Names should be hierarchical
    assert parent_logger.name == "glcs"
    assert child_logger.name == "glcs.core"
    assert grandchild_logger.name == "glcs.core.memory"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

def test_log_rotation_config():
    """Test that log rotation is correctly configured."""
    reset_logging()
    setup_logging("config/logging.yaml")
    
    # Check glcs logger handlers
    logger = logging.getLogger("glcs")
    rotating_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
    
    # We expect 2: 'file' and 'error_file'
    assert len(rotating_handlers) == 2
    
    for handler in rotating_handlers:
        assert handler.maxBytes == 10485760
        assert handler.backupCount == 5
