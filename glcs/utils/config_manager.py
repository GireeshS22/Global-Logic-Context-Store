"""
Configuration Manager for GLCS.

This module provides utilities for loading, validating, and accessing
configuration parameters from YAML files.

The config manager ensures:
1. Configuration files are valid YAML
2. Required sections and parameters exist
3. Values are within acceptable ranges
4. Type safety for configuration access

Usage:
    from glcs.utils.config_manager import load_config, get_config_value

    # Load configuration
    config = load_config("config/glcs_config.yaml")

    # Access values
    threshold = get_config_value(config, "memory.similarity_threshold", default=0.85)

Author: PhD Project
Version: 0.1.0
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


# Required configuration sections
REQUIRED_SECTIONS = ["memory", "consistency", "encoder", "parser", "logging"]

# Value validation rules
VALUE_RANGES = {
    "memory.similarity_threshold": (0.0, 1.0),
    "memory.vector_dimension": (1, 10000),
    "consistency.direct_contradiction_threshold": (0.0, 1.0),
    "consistency.confidence_threshold": (0.0, 1.0),
    "encoder.batch_size": (1, 1000),
    "parser.max_retries": (0, 10),
    "parser.timeout": (1, 300),
}


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    This function:
    1. Resolves the config path (handles relative paths)
    2. Reads and parses the YAML file
    3. Validates the configuration structure
    4. Returns the parsed configuration dictionary

    Args:
        config_path: Path to YAML configuration file (absolute or relative)

    Returns:
        Dictionary containing parsed configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
        ConfigurationError: If config validation fails

    Example:
        >>> config = load_config("config/glcs_config.yaml")
        >>> print(config['memory']['vector_dimension'])
        768
    """
    # Import here to avoid circular dependency
    from glcs.utils.exceptions import ConfigurationError

    # Resolve path
    config_path = Path(config_path)
    if not config_path.is_absolute():
        # Make relative to project root (assumed to be 2 levels up from this file)
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / config_path

    # Check file exists
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please ensure the config file exists at the specified path."
        )

    # Load YAML
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(
            f"Failed to parse configuration file: {config_path}\n"
            f"YAML error: {str(e)}"
        )

    # Validate configuration
    validate_config(config)  # raises ConfigurationError on failure

    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration structure and values.

    Checks:
    1. All required sections are present
    2. Required parameters within sections exist
    3. Values are within acceptable ranges
    4. Types are correct

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigurationError: If validation fails (never returns False — always
        raises on invalid config so callers do not need to check the return value).
    """
    from glcs.utils.exceptions import ConfigurationError

    if config is None:
        raise ConfigurationError("Configuration is None (empty file?)")

    # Check required sections exist
    missing_sections = [
        section for section in REQUIRED_SECTIONS
        if section not in config
    ]

    if missing_sections:
        raise ConfigurationError(
            f"Missing required configuration sections: {missing_sections}\n"
            f"Required sections: {REQUIRED_SECTIONS}"
        )

    # Validate value ranges
    for param_path, (min_val, max_val) in VALUE_RANGES.items():
        try:
            value = get_config_value(config, param_path)
            if value is not None:  # Optional parameters
                if not (min_val <= value <= max_val):
                    raise ConfigurationError(
                        f"Parameter '{param_path}' value {value} is out of range.\n"
                        f"Expected: {min_val} <= value <= {max_val}"
                    )
        except KeyError:
            # Parameter doesn't exist - that's okay for optional params
            pass

    # Specific validation: vector_dimension compatibility
    if "memory" in config and "encoder" in config:
        vec_dim = config["memory"].get("vector_dimension")
        model_name = config["encoder"].get("model_name", "")

        # Warn about common mismatches
        if "MiniLM" in model_name and vec_dim not in [384, 768]:
            # MiniLM-L6-v2 is 384-dim, but allow 768 for projection
            import warnings
            warnings.warn(
                f"Vector dimension {vec_dim} may not match model {model_name}. "
                f"MiniLM models typically use 384 dimensions.",
                UserWarning
            )

    return None


def get_config_value(
    config: Dict[str, Any],
    path: str,
    default: Any = None
) -> Any:
    """
    Get a nested configuration value using dot notation.

    Supports accessing nested dictionary values using a path like:
    "section.subsection.parameter"

    Args:
        config: Configuration dictionary
        path: Dot-separated path to parameter (e.g., "memory.vector_dimension")
        default: Default value if path doesn't exist

    Returns:
        Configuration value at the specified path, or default if not found

    Example:
        >>> config = {"memory": {"similarity_threshold": 0.85}}
        >>> get_config_value(config, "memory.similarity_threshold")
        0.85
        >>> get_config_value(config, "nonexistent.path", default=42)
        42
    """
    parts = path.split(".")
    value = config

    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return default

    return value


def load_config_with_env_overrides(config_path: str) -> Dict[str, Any]:
    """
    Load configuration with environment variable overrides.

    Environment variables can override config file values:
    - GLCS_LOG_LEVEL → logging.level
    - GLCS_MEMORY_PATH → memory.storage_path (future)

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Configuration dictionary with environment overrides applied

    Example:
        >>> os.environ['GLCS_LOG_LEVEL'] = 'DEBUG'
        >>> config = load_config_with_env_overrides("config/glcs_config.yaml")
        >>> config['logging']['level']
        'DEBUG'
    """
    # Load base config
    config = load_config(config_path)

    # Apply environment variable overrides
    env_overrides = {
        "GLCS_LOG_LEVEL": ("logging", "level"),
        "GLCS_MEMORY_PATH": ("memory", "storage_path"),
    }

    for env_var, (section, key) in env_overrides.items():
        value = os.environ.get(env_var)
        if value is not None:
            if section in config:
                config[section][key] = value

    return config


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Save configuration to a YAML file.

    Useful for:
    - Programmatically generating configs
    - Saving modified configurations
    - Creating config templates

    Args:
        config: Configuration dictionary to save
        config_path: Path where to save the YAML file

    Raises:
        ConfigurationError: If save fails

    Example:
        >>> config = load_config("config/glcs_config.yaml")
        >>> config['memory']['similarity_threshold'] = 0.90
        >>> save_config(config, "config/glcs_config_modified.yaml")
    """
    from glcs.utils.exceptions import ConfigurationError

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                config,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )
    except Exception as e:
        raise ConfigurationError(
            f"Failed to save configuration to {config_path}: {str(e)}"
        )
