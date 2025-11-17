"""
Factory for creating LLM provider instances.
"""

from typing import Dict, Type, Optional
from glcs.providers.base import LLMProvider, ProviderConfig, ProviderConfigError


class ProviderFactory:
    """Factory for creating LLM providers

    This factory manages provider registration and instantiation.
    """

    _providers: Dict[str, Type[LLMProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type[LLMProvider]) -> None:
        """Register a provider class

        Args:
            name: Provider name (e.g., 'openai', 'anthropic')
            provider_class: Provider class to register

        Raises:
            ValueError: If provider name is already registered
        """
        if name in cls._providers:
            raise ValueError(f"Provider '{name}' is already registered")

        cls._providers[name] = provider_class

    @classmethod
    def create(cls,
               provider_name: str,
               config: Optional[ProviderConfig] = None,
               **kwargs) -> LLMProvider:
        """Create a provider instance

        Args:
            provider_name: Name of the provider to create
            config: Provider configuration (optional)
            **kwargs: Configuration parameters (if config not provided)

        Returns:
            Provider instance

        Raises:
            ProviderConfigError: If provider is not registered or config is invalid
        """
        if provider_name not in cls._providers:
            available = ', '.join(cls._providers.keys())
            raise ProviderConfigError(
                f"Unknown provider: '{provider_name}'. "
                f"Available providers: {available}"
            )

        # Create config from kwargs if not provided
        if config is None:
            config = ProviderConfig(**kwargs)

        provider_class = cls._providers[provider_name]
        provider = provider_class(config)

        # Validate configuration
        if not provider.validate_config():
            raise ProviderConfigError(
                f"Invalid configuration for provider '{provider_name}'"
            )

        return provider

    @classmethod
    def list_providers(cls) -> list:
        """Get list of registered providers

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a provider is registered

        Args:
            name: Provider name

        Returns:
            True if provider is registered, False otherwise
        """
        return name in cls._providers

    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister a provider

        Args:
            name: Provider name to unregister

        Raises:
            ValueError: If provider is not registered
        """
        if name not in cls._providers:
            raise ValueError(f"Provider '{name}' is not registered")

        del cls._providers[name]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered providers

        Warning: This is primarily for testing purposes
        """
        cls._providers.clear()
