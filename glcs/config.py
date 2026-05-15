"""
Configuration loader for GLCS.

Unified configuration system that handles:
1. Loading from YAML (config/glcs_config.yaml)
2. Environment variable overrides
3. Structural and value validation
4. Default fallback values
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

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


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime and numpy objects."""
    def default(self, obj):
        import numpy as np
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


class ConfigLoader:
    """Load and manage GLCS configuration."""

    DEFAULT_CONFIG_PATH = "config/glcs_config.yaml"

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration loader."""
        self.config_path = self._resolve_path(config_path or self.DEFAULT_CONFIG_PATH)
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _resolve_path(self, path_str: str) -> Path:
        """Resolve path relative to project root."""
        p = Path(path_str)
        if p.is_absolute():
            return p
        
        # Assume project root is parent of 'glcs'
        project_root = Path(__file__).parent.parent
        return project_root / p

    def _load_config(self) -> None:
        """Load configuration from YAML file with environment overrides."""
        # Check if config file exists
        if not self.config_path.exists():
            # (#64: Make sure we raise if file specifically requested doesn't exist)
            if self.config_path.name != "glcs_config.yaml":
                 raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            logger.warning(f"Config file not found: {self.config_path}. Using defaults.")
            self.config = self._get_default_config()
        else:
            # Load YAML file
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
                    if self.config is None: # Handle empty files
                        self.config = {}
            except Exception as e:
                from glcs.utils.exceptions import ConfigurationError
                raise ConfigurationError(f"Failed to parse configuration file '{self.config_path}': {e}")

        # Apply environment variable overrides (Stage 1.4 style overrides)
        self._apply_env_overrides()
        
        # Apply recursive template substitution if any
        self._substitute_env_vars(self.config)
        
        # Validate
        self.validate()

    def _apply_env_overrides(self) -> None:
        """Apply top-level environment overrides."""
        # Provider overrides
        if os.getenv('GLCS_DEFAULT_PROVIDER'):
            self.config.setdefault('parser', {})['llm_provider'] = os.getenv('GLCS_DEFAULT_PROVIDER')
        
        if os.getenv('GLCS_TEMPERATURE'):
            self.config.setdefault('parser', {})['temperature'] = float(os.getenv('GLCS_TEMPERATURE'))

        if os.getenv('GLCS_MAX_TOKENS'):
            self.config.setdefault('parser', {})['max_tokens'] = int(os.getenv('GLCS_MAX_TOKENS'))

        if os.getenv('GLCS_LOG_LEVEL'):
            self.config.setdefault('logging', {})['level'] = os.getenv('GLCS_LOG_LEVEL')

    def _substitute_env_vars(self, config: Any) -> None:
        r"""Recursively substitute ${VAR} patterns in config."""

        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    config[key] = os.getenv(env_var, '')
                elif isinstance(value, (dict, list)):
                    self._substitute_env_vars(value)
        elif isinstance(config, list):
            for item in config:
                self._substitute_env_vars(item)

    def _get_default_config(self) -> Dict[str, Any]:
        """Get hardcoded default configuration."""
        return {
            'memory': {
                'vector_dimension': 768,
                'similarity_threshold': 0.85,
                'initial_capacity': 1000,
            },
            'consistency': {
                'direct_contradiction_threshold': 0.85,
                'confidence_threshold': 0.5,
            },
            'encoder': {
                'model_name': "all-mpnet-base-v2",
                'batch_size': 32,
                'cache_embeddings': True,
            },
            'parser': {
                'llm_provider': "ollama",
                'model': "qwen2.5:0.5b",
                'max_retries': 3,
                'timeout': 30,
                'cache_enabled': True,
                'temperature': 0.1,
                'max_tokens': 300,
            },
            'logging': {
                'level': "INFO",
                'format': "simple",
                'log_file': "glcs.log",
            }
        }

    def validate(self) -> None:
        """Validate configuration structure and values."""
        from glcs.utils.exceptions import ConfigurationError
        
        if self.config is None:
            raise ConfigurationError("Configuration is None")

        # Check required sections
        missing = [section for section in REQUIRED_SECTIONS if section not in self.config]
        if missing:
            # For backward compatibility with some tests, we raise if it's not a patchable scenario
            raise ConfigurationError(f"Missing required configuration sections: {missing}")

        # Validate ranges
        for path, (min_v, max_v) in VALUE_RANGES.items():
            val = self.get_value(path)
            if val is not None and isinstance(val, (int, float)):
                if not (min_v <= val <= max_v):
                    raise ConfigurationError(f"Config '{path}' value {val} out of range [{min_v}, {max_v}]")

    def get_value(self, path: str, default: Any = None) -> Any:
        """Get nested value using dot notation."""
        parts = path.split(".")
        value = self.config
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value

    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Backward compatibility for Stage 1.4 LLM wrapper."""
        # Stage 1.4 expected a flat 'providers' dict.
        # We now use env vars mostly, but we can synthesize it.
        base = self.config.get('parser', {})
        
        # Map provider-specific keys
        cfg = {
            'model': os.getenv(f'{provider_name.upper()}_MODEL', base.get('model')),
            'temperature': base.get('temperature', 0.1),
            'max_tokens': base.get('max_tokens', 300),
            'timeout': base.get('timeout', 30),
            'api_key': os.getenv(f'{provider_name.upper()}_API_KEY', os.getenv('GOOGLE_API_KEY' if provider_name=='gemini' else '')),
        }
        
        if provider_name == 'ollama':
            cfg['endpoint'] = os.getenv('OLLAMA_ENDPOINT', 'http://localhost:11434')
            
        return cfg

    def get_default_provider(self) -> str:
        return self.get_value("parser.llm_provider", "ollama")

    def get_memory_config(self) -> Dict[str, Any]:
        return self.config.get('memory', {})

    def get_logging_config(self) -> Dict[str, Any]:
        return self.config.get('logging', {})


# Global instance
_config_instance: Optional[ConfigLoader] = None

def get_config(config_path: Optional[str] = None) -> ConfigLoader:
    global _config_instance
    if _config_instance is None or config_path is not None:
        _config_instance = ConfigLoader(config_path)
    return _config_instance

def reload_config(config_path: Optional[str] = None) -> ConfigLoader:
    global _config_instance
    _config_instance = ConfigLoader(config_path)
    return _config_instance
