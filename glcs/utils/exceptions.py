"""
Custom Exception Hierarchy for GLCS.

This module defines all custom exceptions used throughout the GLCS system.
All GLCS exceptions inherit from GLCSException for easy catching.

Exception Hierarchy:
    GLCSException (base)
    ├── ConfigurationError      - Configuration issues
    ├── GLCSMemoryError        - Memory operations failures
    ├── ConsistencyError       - Consistency checking failures
    ├── ValidationError        - Data validation failures
    └── ParsingError           - Parsing failures

Usage:
    from glcs.utils.exceptions import ConfigurationError

    # Raise specific exception
    if config is None:
        raise ConfigurationError("Configuration file is empty")

    # Catch specific exception
    try:
        config = load_config("config.yaml")
    except ConfigurationError as e:
        logger.error(f"Config error: {e}")

    # Catch any GLCS exception
    try:
        process_statement(text)
    except GLCSException as e:
        logger.error(f"GLCS error: {e}")

Author: PhD Project
Version: 0.1.0
"""


class GLCSException(Exception):
    """
    Base exception for all GLCS errors.

    All custom GLCS exceptions inherit from this class.
    This allows catching any GLCS-specific error with a single except clause.

    Example:
        >>> raise GLCSException("Something went wrong in GLCS")

        >>> try:
        ...     # Some GLCS operation
        ...     pass
        ... except GLCSException as e:
        ...     print(f"GLCS error occurred: {e}")
    """
    pass


class ConfigurationError(GLCSException):
    """
    Raised when configuration is invalid or cannot be loaded.

    Common scenarios:
    - Configuration file not found
    - Invalid YAML syntax
    - Missing required configuration sections
    - Invalid parameter values (out of range, wrong type)

    Example:
        >>> if 'memory' not in config:
        ...     raise ConfigurationError("Missing 'memory' section in config")

        >>> if similarity_threshold > 1.0:
        ...     raise ConfigurationError(
        ...         f"similarity_threshold must be <= 1.0, got {similarity_threshold}"
        ...     )
    """
    pass


class GLCSMemoryError(GLCSException):
    """
    Raised when memory operations fail.

    Common scenarios:
    - Memory is full and eviction fails
    - Vector dimension mismatch
    - Corrupted memory state
    - Failed to save/load memory

    Example:
        >>> if vector.shape[0] != expected_dim:
        ...     raise GLCSMemoryError(
        ...         f"Vector dimension mismatch: expected {expected_dim}, "
        ...         f"got {vector.shape[0]}"
        ...     )

        >>> if not self.can_write():
        ...     raise GLCSMemoryError("Memory is full and eviction failed")
    """
    pass


class ConsistencyError(GLCSException):
    """
    Raised when consistency checking encounters an error.

    Note: This is for errors in the consistency checking process itself,
    not for detected contradictions (which are returned in ConsistencyReport).

    Common scenarios:
    - Invalid logical form structure
    - Consistency algorithm failure
    - Missing required fields for consistency check

    Example:
        >>> if logical_form.subject is None:
        ...     raise ConsistencyError(
        ...         "Cannot check consistency: logical form has no subject"
        ...     )

        >>> if similarity_results is None:
        ...     raise ConsistencyError("Failed to retrieve similar statements from memory")
    """
    pass


class ValidationError(GLCSException):
    """
    Raised when data validation fails.

    Common scenarios:
    - Invalid LogicalForm structure
    - Missing required fields in Pydantic models
    - Type mismatches
    - Constraint violations

    Example:
        >>> if not isinstance(polarity, Polarity):
        ...     raise ValidationError(
        ...         f"polarity must be Polarity enum, got {type(polarity)}"
        ...     )

        >>> if context_id is None or context_id == "":
        ...     raise ValidationError("context_id cannot be empty")
    """
    pass


class ParsingError(GLCSException):
    """
    Raised when parsing natural language to LogicalForm fails.

    Common scenarios:
    - LLM API failure (timeout, rate limit, invalid API key)
    - LLM returns invalid JSON
    - Cannot extract logical structure from text
    - Ambiguous or unparseable statements

    Example:
        >>> if api_response.status_code != 200:
        ...     raise ParsingError(
        ...         f"LLM API request failed with status {api_response.status_code}"
        ...     )

        >>> if not is_valid_json(llm_output):
        ...     raise ParsingError(
        ...         f"LLM returned invalid JSON: {llm_output}"
        ...     )
    """
    pass


# Exception handling utilities

def format_exception_message(
    exception: Exception,
    context: str = "",
    suggestions: list[str] = None
) -> str:
    """
    Format an exception message with context and suggestions.

    Args:
        exception: The exception to format
        context: Additional context about where/why the error occurred
        suggestions: List of suggestions for fixing the error

    Returns:
        Formatted error message string

    Example:
        >>> try:
        ...     config = load_config("missing.yaml")
        ... except FileNotFoundError as e:
        ...     msg = format_exception_message(
        ...         e,
        ...         context="Loading GLCS configuration",
        ...         suggestions=[
        ...             "Check that config/glcs_config.yaml exists",
        ...             "Run: cp config/glcs_config.yaml.template config/glcs_config.yaml"
        ...         ]
        ...     )
        ...     print(msg)
    """
    lines = []

    # Exception type and message
    lines.append(f"[{exception.__class__.__name__}] {str(exception)}")

    # Context
    if context:
        lines.append(f"\nContext: {context}")

    # Suggestions
    if suggestions:
        lines.append("\nSuggestions:")
        for suggestion in suggestions:
            lines.append(f"  - {suggestion}")

    return "\n".join(lines)
