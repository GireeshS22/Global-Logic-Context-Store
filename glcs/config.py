"""
Configuration loader for GLCS.

Loads configuration from YAML files and environment variables.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ConfigLoader:
    """Load and manage GLCS configuration

    Configuration is loaded from:
    1. Default config file (config/glcs_config.yaml)
    2. Environment variables (override YAML)
    """

    DEFAULT_CONFIG_PATH = "config/glcs_config.yaml"

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration loader

        Args:
            config_path: Path to config file (optional)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        # Check if config file exists
        if not os.path.exists(self.config_path):
            # Use default configuration
            self.config = self._get_default_config()
            return

        # Load YAML file
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        except Exception as e:
            raise ValueError(f"Error loading config file '{self.config_path}': {e}")

        # Substitute environment variables
        self._substitute_env_vars(self.config)

    def _substitute_env_vars(self, config: Any) -> None:
        """Recursively substitute environment variables in config

        Args:
            config: Configuration dict to process
        """
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    # Extract env var name
                    env_var = value[2:-1]
                    # Substitute with env value
                    config[key] = os.getenv(env_var, '')
                elif isinstance(value, (dict, list)):
                    self._substitute_env_vars(value)
        elif isinstance(config, list):
            for item in config:
                self._substitute_env_vars(item)

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration

        Returns:
            Default configuration dict
        """
        return {
            'default_provider': os.getenv('GLCS_DEFAULT_PROVIDER', 'openai'),
            'providers': {
                'openai': {
                    'api_key': os.getenv('OPENAI_API_KEY', ''),
                    'model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                    'temperature': float(os.getenv('GLCS_TEMPERATURE', '0.7')),
                    'max_tokens': int(os.getenv('GLCS_MAX_TOKENS', '150')),
                    'timeout': 30,
                },
                'anthropic': {
                    'api_key': os.getenv('ANTHROPIC_API_KEY', ''),
                    'model': os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),
                    'temperature': float(os.getenv('GLCS_TEMPERATURE', '0.7')),
                    'max_tokens': int(os.getenv('GLCS_MAX_TOKENS', '150')),
                    'timeout': 30,
                },
                'gemini': {
                    'api_key': os.getenv('GOOGLE_API_KEY', ''),
                    'model': os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'),
                    'temperature': float(os.getenv('GLCS_TEMPERATURE', '0.7')),
                    'max_tokens': int(os.getenv('GLCS_MAX_TOKENS', '150')),
                    'timeout': 30,
                },
                'groq': {
                    'api_key': os.getenv('GROQ_API_KEY', ''),
                    'model': os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768'),
                    'temperature': float(os.getenv('GLCS_TEMPERATURE', '0.7')),
                    'max_tokens': int(os.getenv('GLCS_MAX_TOKENS', '150')),
                    'timeout': 30,
                },
                'ollama': {
                    'endpoint': os.getenv('OLLAMA_ENDPOINT', 'http://localhost:11434'),
                    'model': os.getenv('OLLAMA_MODEL', 'llama3.2'),
                    'temperature': float(os.getenv('GLCS_TEMPERATURE', '0.7')),
                    'max_tokens': int(os.getenv('GLCS_MAX_TOKENS', '150')),
                    'timeout': 60,
                },
            },
            'memory': {
                'persist_path': os.getenv('GLCS_MEMORY_PATH', 'glcs_memory.json'),
                'auto_save': True,
                'max_statements': 10000,
            },
            'logging': {
                'level': os.getenv('GLCS_LOG_LEVEL', 'INFO'),
                'file': os.getenv('GLCS_LOG_FILE', 'glcs.log'),
                'console': True,
            },
        }

    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Get configuration for a specific provider

        Args:
            provider_name: Name of provider

        Returns:
            Provider configuration dict

        Raises:
            ValueError: If provider not found in config
        """
        providers = self.config.get('providers', {})

        if provider_name not in providers:
            raise ValueError(
                f"Provider '{provider_name}' not found in configuration. "
                f"Available providers: {', '.join(providers.keys())}"
            )

        return providers[provider_name]

    def get_default_provider(self) -> str:
        """Get default provider name

        Returns:
            Default provider name
        """
        return self.config.get('default_provider', 'openai')

    def get_memory_config(self) -> Dict[str, Any]:
        """Get memory configuration

        Returns:
            Memory configuration dict
        """
        return self.config.get('memory', {
            'persist_path': 'glcs_memory.json',
            'auto_save': True,
        })

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration

        Returns:
            Logging configuration dict
        """
        return self.config.get('logging', {
            'level': 'INFO',
            'file': 'glcs.log',
            'console': True,
        })

    def list_providers(self) -> list:
        """List all configured providers

        Returns:
            List of provider names
        """
        return list(self.config.get('providers', {}).keys())

    def is_provider_configured(self, provider_name: str) -> bool:
        """Check if a provider is properly configured

        Args:
            provider_name: Provider name

        Returns:
            True if provider is configured with API key (or no key needed)
        """
        try:
            provider_config = self.get_provider_config(provider_name)

            # Ollama doesn't need API key
            if provider_name == 'ollama':
                return True

            # Other providers need API key
            api_key = provider_config.get('api_key', '')
            return bool(api_key and api_key != '')

        except ValueError:
            return False


# Global config instance
_config_instance: Optional[ConfigLoader] = None


def get_config(config_path: Optional[str] = None) -> ConfigLoader:
    """Get global configuration instance

    Args:
        config_path: Path to config file (optional)

    Returns:
        ConfigLoader instance
    """
    global _config_instance

    if _config_instance is None or config_path is not None:
        _config_instance = ConfigLoader(config_path)

    return _config_instance


def reload_config(config_path: Optional[str] = None) -> ConfigLoader:
    """Reload configuration

    Args:
        config_path: Path to config file (optional)

    Returns:
        New ConfigLoader instance
    """
    global _config_instance
    _config_instance = ConfigLoader(config_path)
    return _config_instance
