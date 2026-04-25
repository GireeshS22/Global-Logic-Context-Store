"""
xAI (Grok) provider implementation for GLCS.

Uses the OpenAI-compatible API at https://api.x.ai/v1.
Requires XAI_API_KEY environment variable.
"""

from typing import Dict, Any
from glcs.providers.base import (
    OpenAICompatibleProvider,
    ProviderConfig,
    ProviderError,
    ProviderConfigError,
    ProviderAPIError,
    ProviderTimeoutError,
    ProviderRateLimitError,
)

try:
    import openai as _openai_sdk
    _OPENAI_TIMEOUT_ERROR = _openai_sdk.APITimeoutError
    _OPENAI_RATE_LIMIT_ERROR = _openai_sdk.RateLimitError
    _OPENAI_API_ERROR = _openai_sdk.APIError
except (ImportError, AttributeError):
    _OPENAI_TIMEOUT_ERROR = None
    _OPENAI_RATE_LIMIT_ERROR = None
    _OPENAI_API_ERROR = None

_XAI_BASE_URL = "https://api.x.ai/v1"


class XAIProvider(OpenAICompatibleProvider):
    """xAI Grok LLM provider (OpenAI-compatible API).

    Supports xAI Grok models:
    - grok-3-mini
    - grok-3
    - grok-2
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        if not self.config.model:
            self.config.model = "grok-3-mini"

        if not self.config.api_key:
            raise ProviderConfigError(
                "xAI API key is required. Set XAI_API_KEY or pass api_key."
            )

        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=_XAI_BASE_URL,
                timeout=self.config.timeout,
            )
        except ImportError:
            raise ProviderError(
                "OpenAI package not installed (required for xAI). "
                "Install with: pip install openai"
            )

    def _classify_error(self, e: Exception) -> ProviderError:
        if _OPENAI_TIMEOUT_ERROR and isinstance(e, _OPENAI_TIMEOUT_ERROR):
            return ProviderTimeoutError(f"xAI request timed out: {e}")
        if _OPENAI_RATE_LIMIT_ERROR and isinstance(e, _OPENAI_RATE_LIMIT_ERROR):
            return ProviderRateLimitError(f"xAI rate limit exceeded: {e}")
        if _OPENAI_API_ERROR and isinstance(e, _OPENAI_API_ERROR):
            return ProviderAPIError(f"xAI API error: {e}")
        return super()._classify_error(e)

    def get_provider_name(self) -> str:
        return "xai"

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info['base_url'] = _XAI_BASE_URL
        info['supports_streaming'] = True
        return info
