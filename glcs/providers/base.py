"""
Base provider abstraction for LLM providers in GLCS.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider"""
    api_key: Optional[str] = None
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 150
    timeout: int = 30
    extra: Dict[str, Any] = field(default_factory=dict)  # #83: avoid mutable default

    def __repr__(self):
        masked_key = "***" if self.api_key else None
        return f"ProviderConfig(api_key={masked_key}, model={self.model!r}, temperature={self.temperature}, max_tokens={self.max_tokens}, timeout={self.timeout}, extra={self.extra})"


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


class OpenAICompatibleProvider(LLMProvider):
    """Base class for providers that use the OpenAI-compatible chat completions API.

    Eliminates the copy-paste generate() between OpenAI and Groq providers (#28).
    Subclasses implement _create_client() and may override _classify_error() for
    typed SDK exception handling (#24).
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            params = {
                'model': kwargs.get('model', self.config.model),
                'messages': messages,
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            }
            for key, value in kwargs.items():
                if key not in params:
                    params[key] = value
            response = self._client.chat.completions.create(**params)
            return response.choices[0].message.content
        except ProviderError:
            raise
        except Exception as e:
            raise self._classify_error(e)

    def _classify_error(self, e: Exception) -> 'ProviderError':
        """Map an SDK exception to a ProviderError subclass.

        Override in subclasses to catch typed SDK exceptions before falling
        back to string-based classification (#24).
        """
        error_msg = str(e).lower()
        if 'timeout' in error_msg:
            return ProviderTimeoutError(
                f"{self.get_provider_name()} request timed out: {e}"
            )
        if 'rate limit' in error_msg or 'quota' in error_msg or '429' in error_msg:
            return ProviderRateLimitError(
                f"{self.get_provider_name()} rate limit exceeded: {e}"
            )
        return ProviderAPIError(f"{self.get_provider_name()} API error: {e}")

    def validate_config(self) -> bool:
        return bool(self.config.api_key and self.config.model)
