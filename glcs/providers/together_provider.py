"""
Together AI provider implementation for GLCS.

Uses the OpenAI-compatible API at https://api.together.xyz/v1.
Requires TOGETHER_API_KEY environment variable.
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

_TOGETHER_BASE_URL = "https://api.together.xyz/v1"


class TogetherProvider(OpenAICompatibleProvider):
    """Together AI LLM provider (OpenAI-compatible API).

    Supports open-source models hosted on Together AI:
    - meta-llama/Llama-3.3-70B-Instruct-Turbo
    - mistralai/Mixtral-8x7B-Instruct-v0.1
    - Qwen/Qwen2.5-72B-Instruct-Turbo
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        if not self.config.model:
            self.config.model = "meta-llama/Llama-3.3-70B-Instruct-Turbo"

        if not self.config.api_key:
            raise ProviderConfigError(
                "Together AI API key is required. Set TOGETHER_API_KEY or pass api_key."
            )

        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=_TOGETHER_BASE_URL,
                timeout=self.config.timeout,
            )
        except ImportError:
            raise ProviderError(
                "OpenAI package not installed (required for Together AI). "
                "Install with: pip install openai"
            )

    def _classify_error(self, e: Exception) -> ProviderError:
        if _OPENAI_TIMEOUT_ERROR and isinstance(e, _OPENAI_TIMEOUT_ERROR):
            return ProviderTimeoutError(f"Together AI request timed out: {e}")
        if _OPENAI_RATE_LIMIT_ERROR and isinstance(e, _OPENAI_RATE_LIMIT_ERROR):
            return ProviderRateLimitError(f"Together AI rate limit exceeded: {e}")
        if _OPENAI_API_ERROR and isinstance(e, _OPENAI_API_ERROR):
            return ProviderAPIError(f"Together AI API error: {e}")
        return super()._classify_error(e)

    def get_provider_name(self) -> str:
        return "together"

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info['base_url'] = _TOGETHER_BASE_URL
        info['supports_streaming'] = True
        return info
