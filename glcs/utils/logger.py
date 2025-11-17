"""
Logging Utility for GLCS.

This module provides centralized logging configuration and logger instances
for all GLCS components.

Features:
- Loads logging configuration from YAML file
- Provides consistent logger instances across modules
- Supports multiple log handlers (console, file, error file)
- Configurable log levels and formats

Usage:
    from glcs.utils.logger import get_logger

    # In each module, get a logger with the module name
    logger = get_logger(__name__)

    # Log messages at different levels
    logger.debug("Detailed debug information")
    logger.info("General information")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical error")

Author: PhD Project
Version: 0.1.0
"""

import logging
import logging.config
from pathlib import Path
from typing import Optional
import yaml


# Global flag to track if logging has been set up
_logging_configured = False


def setup_logging(config_path: str = "config/logging.yaml") -> None:
    """
    Set up logging configuration from YAML file.

    This function should be called once at application startup.
    It configures all loggers, handlers, and formatters defined
    in the logging configuration file.

    Args:
        config_path: Path to logging configuration YAML file
                     (default: "config/logging.yaml")

    Raises:
        FileNotFoundError: If logging config file doesn't exist
        ValueError: If logging config is invalid

    Example:
        >>> from glcs.utils.logger import setup_logging
        >>> setup_logging("config/logging.yaml")
        >>> # Logging is now configured for the entire application
    """
    global _logging_configured

    # Resolve path
    config_path = Path(config_path)
    if not config_path.is_absolute():
        # Make relative to project root
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / config_path

    # Check file exists
    if not config_path.exists():
        raise FileNotFoundError(
            f"Logging configuration file not found: {config_path}\n"
            f"Please ensure the logging config exists."
        )

    # Load YAML configuration
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            log_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(
            f"Failed to parse logging configuration: {config_path}\n"
            f"YAML error: {str(e)}"
        )

    # Apply configuration
    try:
        logging.config.dictConfig(log_config)
        _logging_configured = True
    except Exception as e:
        raise ValueError(
            f"Failed to apply logging configuration: {str(e)}"
        )


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.

    This is the primary function to use for getting loggers in GLCS.
    It ensures logging is configured and returns a logger with the
    specified name.

    Args:
        name: Logger name (typically __name__ of the calling module)
        level: Optional log level override (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger instance configured according to logging.yaml

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("This is an info message")

        >>> # With level override
        >>> debug_logger = get_logger(__name__, level="DEBUG")
        >>> debug_logger.debug("This is a debug message")
    """
    global _logging_configured

    # Auto-configure logging if not already done
    if not _logging_configured:
        try:
            setup_logging()
        except FileNotFoundError:
            # Fallback to basic configuration if config file not found
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            _logging_configured = True

    # Get logger
    logger = logging.getLogger(name)

    # Apply level override if specified
    if level is not None:
        numeric_level = getattr(logging, level.upper(), None)
        if numeric_level is not None:
            logger.setLevel(numeric_level)

    return logger


def reset_logging() -> None:
    """
    Reset logging configuration.

    Useful for:
    - Testing (reset between tests)
    - Reloading configuration
    - Cleaning up

    Example:
        >>> reset_logging()
        >>> setup_logging("config/logging_test.yaml")
    """
    global _logging_configured

    # Remove all handlers from all loggers
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)

    # Clear root logger handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    _logging_configured = False
