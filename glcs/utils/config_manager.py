"""
Configuration Manager for GLCS (Compatibility Bridge).

This module is now a bridge to the unified configuration system in glcs/config.py.
It maintains the original API for backward compatibility.
"""

from typing import Any, Dict, Optional
from glcs.config import get_config, ConfigLoader, DateTimeEncoder


def load_config(config_path: str) -> Dict[str, Any]:
    """Backward compatibility for loading config dict."""
    loader = ConfigLoader(config_path)
    return loader.config


def validate_config(config: Dict[str, Any]) -> None:
    """Backward compatibility for validation."""
    # We use a dummy loader to leverage its validation logic
    loader = ConfigLoader()
    loader.config = config
    loader.validate()


def get_config_value(
    config: Dict[str, Any],
    path: str,
    default: Any = None
) -> Any:
    """Backward compatibility for dot-notation access."""
    parts = path.split(".")
    value = config
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return default
    return value


def load_config_with_env_overrides(config_path: str) -> Dict[str, Any]:
    """Backward compatibility for env overrides."""
    return load_config(config_path)


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """Save configuration to a YAML file."""
    import yaml
    from glcs.utils.exceptions import ConfigurationError
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise ConfigurationError(f"Failed to save configuration: {e}")
