"""
OpenAI provider implementation for GLCS.

Supports GPT-4o, GPT-4o-mini, GPT-3.5-turbo, and other OpenAI models.
"""

from typing import List, Dict, Any
from glcs.providers.base import (
    OpenAICompatibleProvider,
    ProviderConfig,
    ProviderError,
    ProviderConfigError,
    ProviderAPIError,
    ProviderTimeoutError,
    ProviderRateLimitError,
)

# Import typed SDK exceptions for proper error classification (#24)
try:
    import openai as _openai_sdk
    _OPENAI_TIMEOUT_ERROR = _openai_sdk.APITimeoutError
    _OPENAI_RATE_LIMIT_ERROR = _openai_sdk.RateLimitError
    _OPENAI_API_ERROR = _openai_sdk.APIError
except (ImportError, AttributeError):
    _OPENAI_TIMEOUT_ERROR = None
    _OPENAI_RATE_LIMIT_ERROR = None
    _OPENAI_API_ERROR = None


class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI LLM provider

    Supports all OpenAI chat models including:
    - gpt-4o
    - gpt-4o-mini
    - gpt-3.5-turbo
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        if not self.config.model:
            self.config.model = "gpt-4o-mini"

        # Validate config before creating client (#27)
        if not self.config.api_key:
            raise ProviderConfigError(
                "OpenAI API key is required. Set OPENAI_API_KEY or pass api_key."
            )

        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
        except ImportError:
            raise ProviderError(
                "OpenAI package not installed. "
                "Install with: pip install openai"
            )

    def _classify_error(self, e: Exception) -> ProviderError:
        """Use typed openai SDK exceptions where available (#24)."""
        if _OPENAI_TIMEOUT_ERROR and isinstance(e, _OPENAI_TIMEOUT_ERROR):
            return ProviderTimeoutError(f"OpenAI request timed out: {e}")
        if _OPENAI_RATE_LIMIT_ERROR and isinstance(e, _OPENAI_RATE_LIMIT_ERROR):
            return ProviderRateLimitError(f"OpenAI rate limit exceeded: {e}")
        if _OPENAI_API_ERROR and isinstance(e, _OPENAI_API_ERROR):
            return ProviderAPIError(f"OpenAI API error: {e}")
        # Fallback to string matching
        return super()._classify_error(e)

    def get_provider_name(self) -> str:
        return "openai"

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info['supports_streaming'] = True
        info['supports_functions'] = True
        info['context_window'] = self._get_context_window()
        return info

    def _get_context_window(self) -> int:
        context_windows = {
            'gpt-4o': 128000,
            'gpt-4o-mini': 128000,
            'gpt-4-turbo': 128000,
            'gpt-4': 8192,
            'gpt-3.5-turbo': 16385,
            'gpt-3.5-turbo-16k': 16385,
        }
        return context_windows.get(self.config.model, 4096)
