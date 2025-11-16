"""
Unit tests for custom exceptions.

Tests cover:
- Each exception can be raised and caught
- Exception inheritance
- Exception messages
- Exception utility functions

Author: PhD Project
Version: 0.1.0
"""

import pytest

from glcs.utils.exceptions import (
    GLCSException,
    ConfigurationError,
    MemoryError,
    ConsistencyError,
    ValidationError,
    ParsingError,
    format_exception_message
)


def test_glcs_exception_raised():
    """Test base GLCSException can be raised."""
    with pytest.raises(GLCSException) as exc_info:
        raise GLCSException("Base exception message")

    assert "Base exception message" in str(exc_info.value)


def test_configuration_error_raised():
    """Test ConfigurationError can be raised and caught."""
    with pytest.raises(ConfigurationError) as exc_info:
        raise ConfigurationError("Configuration is invalid")

    assert "Configuration is invalid" in str(exc_info.value)
    assert isinstance(exc_info.value, GLCSException)


def test_memory_error_raised():
    """Test MemoryError can be raised and caught."""
    with pytest.raises(MemoryError) as exc_info:
        raise MemoryError("Memory operation failed")

    assert "Memory operation failed" in str(exc_info.value)
    assert isinstance(exc_info.value, GLCSException)


def test_consistency_error_raised():
    """Test ConsistencyError can be raised and caught."""
    with pytest.raises(ConsistencyError) as exc_info:
        raise ConsistencyError("Consistency check failed")

    assert "Consistency check failed" in str(exc_info.value)
    assert isinstance(exc_info.value, GLCSException)


def test_validation_error_raised():
    """Test ValidationError can be raised and caught."""
    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError("Data validation failed")

    assert "Data validation failed" in str(exc_info.value)
    assert isinstance(exc_info.value, GLCSException)


def test_parsing_error_raised():
    """Test ParsingError can be raised and caught."""
    with pytest.raises(ParsingError) as exc_info:
        raise ParsingError("Failed to parse statement")

    assert "Failed to parse statement" in str(exc_info.value)
    assert isinstance(exc_info.value, GLCSException)


def test_exception_inheritance():
    """Test all exceptions inherit from GLCSException."""
    exceptions = [
        ConfigurationError("test"),
        MemoryError("test"),
        ConsistencyError("test"),
        ValidationError("test"),
        ParsingError("test")
    ]

    for exc in exceptions:
        assert isinstance(exc, GLCSException)
        assert isinstance(exc, Exception)


def test_catch_specific_exception():
    """Test catching specific exception types."""
    def raise_config_error():
        raise ConfigurationError("Config error")

    # Catch specific exception
    try:
        raise_config_error()
        assert False, "Should have raised exception"
    except ConfigurationError as e:
        assert "Config error" in str(e)


def test_catch_base_glcs_exception():
    """Test catching any GLCS exception with base class."""
    def raise_various_errors(error_type):
        if error_type == "config":
            raise ConfigurationError("Config error")
        elif error_type == "memory":
            raise MemoryError("Memory error")
        elif error_type == "validation":
            raise ValidationError("Validation error")

    # Catch with base GLCSException
    for error_type in ["config", "memory", "validation"]:
        try:
            raise_various_errors(error_type)
            assert False, "Should have raised exception"
        except GLCSException as e:
            assert "error" in str(e).lower()


def test_exception_messages():
    """Test exception messages are preserved."""
    test_message = "This is a detailed error message"

    exceptions = [
        GLCSException(test_message),
        ConfigurationError(test_message),
        MemoryError(test_message),
        ConsistencyError(test_message),
        ValidationError(test_message),
        ParsingError(test_message)
    ]

    for exc in exceptions:
        assert str(exc) == test_message


def test_exception_with_formatted_message():
    """Test exceptions with formatted messages."""
    param = "similarity_threshold"
    value = 1.5
    expected_range = "0.0-1.0"

    error = ConfigurationError(
        f"Parameter '{param}' value {value} is out of range. "
        f"Expected: {expected_range}"
    )

    message = str(error)
    assert param in message
    assert str(value) in message
    assert expected_range in message


def test_format_exception_message_basic():
    """Test formatting exception message without context or suggestions."""
    exc = ValueError("Something went wrong")

    formatted = format_exception_message(exc)

    assert "ValueError" in formatted
    assert "Something went wrong" in formatted


def test_format_exception_message_with_context():
    """Test formatting exception message with context."""
    exc = FileNotFoundError("config.yaml not found")

    formatted = format_exception_message(
        exc,
        context="Loading configuration"
    )

    assert "FileNotFoundError" in formatted
    assert "config.yaml not found" in formatted
    assert "Loading configuration" in formatted


def test_format_exception_message_with_suggestions():
    """Test formatting exception message with suggestions."""
    exc = ConfigurationError("Invalid config")

    formatted = format_exception_message(
        exc,
        context="Validating configuration",
        suggestions=[
            "Check config file syntax",
            "Ensure all required sections are present"
        ]
    )

    assert "ConfigurationError" in formatted
    assert "Invalid config" in formatted
    assert "Validating configuration" in formatted
    assert "Check config file syntax" in formatted
    assert "Ensure all required sections are present" in formatted


def test_format_exception_message_full():
    """Test formatting with all components."""
    exc = ParsingError("Failed to parse JSON from LLM")

    formatted = format_exception_message(
        exc,
        context="Processing LLM response",
        suggestions=[
            "Check LLM API key is valid",
            "Verify LLM model supports JSON mode",
            "Check network connectivity"
        ]
    )

    # Should contain all components
    assert "ParsingError" in formatted
    assert "Failed to parse JSON from LLM" in formatted
    assert "Processing LLM response" in formatted
    assert "Suggestions:" in formatted
    assert "Check LLM API key is valid" in formatted


def test_exception_class_names():
    """Test exception class names are correct."""
    assert GLCSException.__name__ == "GLCSException"
    assert ConfigurationError.__name__ == "ConfigurationError"
    assert MemoryError.__name__ == "MemoryError"
    assert ConsistencyError.__name__ == "ConsistencyError"
    assert ValidationError.__name__ == "ValidationError"
    assert ParsingError.__name__ == "ParsingError"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
