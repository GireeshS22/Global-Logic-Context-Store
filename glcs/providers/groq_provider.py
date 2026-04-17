"""
Groq provider implementation for GLCS.

Supports fast inference with Mixtral, Llama, and other models.
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
    import groq as _groq_sdk
    _GROQ_TIMEOUT_ERROR = _groq_sdk.APITimeoutError
    _GROQ_RATE_LIMIT_ERROR = _groq_sdk.RateLimitError
    _GROQ_API_ERROR = _groq_sdk.APIError
except (ImportError, AttributeError):
    _GROQ_TIMEOUT_ERROR = None
    _GROQ_RATE_LIMIT_ERROR = None
    _GROQ_API_ERROR = None


class GroqProvider(OpenAICompatibleProvider):
    """Groq LLM provider

    Groq provides ultra-fast inference for open-source models:
    - mixtral-8x7b-32768
    - llama-3.1-70b-versatile
    - llama-3.1-8b-instant
    - gemma-7b-it
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        if not self.config.model:
            self.config.model = "mixtral-8x7b-32768"

        # Validate config before creating client (#27)
        if not self.config.api_key:
            raise ProviderConfigError(
                "Groq API key is required. Set GROQ_API_KEY or pass api_key."
            )

        try:
            from groq import Groq
            self._client = Groq(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
        except ImportError:
            raise ProviderError(
                "Groq package not installed. "
                "Install with: pip install groq"
            )

    def _classify_error(self, e: Exception) -> ProviderError:
        """Use typed groq SDK exceptions where available (#24)."""
        if _GROQ_TIMEOUT_ERROR and isinstance(e, _GROQ_TIMEOUT_ERROR):
            return ProviderTimeoutError(f"Groq request timed out: {e}")
        if _GROQ_RATE_LIMIT_ERROR and isinstance(e, _GROQ_RATE_LIMIT_ERROR):
            return ProviderRateLimitError(f"Groq rate limit exceeded: {e}")
        if _GROQ_API_ERROR and isinstance(e, _GROQ_API_ERROR):
            return ProviderAPIError(f"Groq API error: {e}")
        # Fallback to string matching
        return super()._classify_error(e)

    def get_provider_name(self) -> str:
        return "groq"

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info['supports_streaming'] = True
        info['ultra_fast'] = True
        info['context_window'] = self._get_context_window()
        return info

    def _get_context_window(self) -> int:
        context_windows = {
            'mixtral-8x7b-32768': 32768,
            'llama-3.1-70b-versatile': 131072,
            'llama-3.1-8b-instant': 131072,
            'gemma-7b-it': 8192,
            'llama3-70b-8192': 8192,
            'llama3-8b-8192': 8192,
        }
        return context_windows.get(self.config.model, 8192)
