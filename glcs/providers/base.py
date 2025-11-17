"""
Base provider abstraction for LLM providers in GLCS.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider"""
    api_key: Optional[str] = None
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 150
    timeout: int = 30
    extra: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}


class LLMProvider(ABC):
    """Abstract base class for LLM providers

    All provider implementations must inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, config: ProviderConfig):
        """Initialize the provider

        Args:
            config: Provider configuration
        """
        self.config = config
        self._client = None

    @abstractmethod
    def generate(self,
                 messages: List[Dict[str, str]],
                 **kwargs) -> str:
        """Generate response from LLM

        Args:
            messages: List of messages in OpenAI format:
                      [{"role": "system|user|assistant", "content": "..."}]
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response

        Raises:
            ProviderError: If generation fails
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate provider configuration

        Returns:
            True if configuration is valid, False otherwise
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name

        Returns:
            Provider name (e.g., 'openai', 'anthropic')
        """
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model

        Returns:
            Dictionary with model information
        """
        return {
            'provider': self.get_provider_name(),
            'model': self.config.model,
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens
        }

    def _convert_messages(self, messages: List[Dict[str, str]]) -> Any:
        """Convert OpenAI-format messages to provider-specific format

        This method can be overridden by providers that use different
        message formats.

        Args:
            messages: Messages in OpenAI format

        Returns:
            Messages in provider-specific format
        """
        return messages


class ProviderError(Exception):
    """Base exception for provider errors"""
    pass


class ProviderConfigError(ProviderError):
    """Exception for configuration errors"""
    pass


class ProviderAPIError(ProviderError):
    """Exception for API errors"""
    pass


class ProviderTimeoutError(ProviderError):
    """Exception for timeout errors"""
    pass


class ProviderRateLimitError(ProviderError):
    """Exception for rate limit errors"""
    pass
