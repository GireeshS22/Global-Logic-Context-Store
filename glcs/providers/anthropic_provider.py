"""
Anthropic Claude provider implementation for GLCS.

Supports Claude 3.5 Sonnet, Claude 3 Opus, and Claude 3 Haiku.
"""

from typing import List, Dict, Any
from glcs.providers.base import (
    LLMProvider,
    ProviderConfig,
    ProviderError,
    ProviderConfigError,
    ProviderAPIError,
    ProviderTimeoutError,
    ProviderRateLimitError,
)

# Import typed SDK exceptions for proper error classification (#24)
try:
    import anthropic as _anthropic_sdk
    _ANTHROPIC_TIMEOUT_ERROR = _anthropic_sdk.APITimeoutError
    _ANTHROPIC_RATE_LIMIT_ERROR = _anthropic_sdk.RateLimitError
    _ANTHROPIC_API_ERROR = _anthropic_sdk.APIError
except (ImportError, AttributeError):
    _ANTHROPIC_TIMEOUT_ERROR = None
    _ANTHROPIC_RATE_LIMIT_ERROR = None
    _ANTHROPIC_API_ERROR = None


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider

    Supports all Claude 3.x models including:
    - claude-3-5-sonnet-20241022
    - claude-3-opus-20240229
    - claude-3-sonnet-20240229
    - claude-3-haiku-20240307
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        if not self.config.model:
            self.config.model = "claude-haiku-4-5-20251001"

        # Validate config before creating client (#27)
        if not self.config.api_key:
            raise ProviderConfigError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY or pass api_key."
            )

        try:
            from anthropic import Anthropic
            self._client = Anthropic(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
        except ImportError:
            raise ProviderError(
                "Anthropic package not installed. "
                "Install with: pip install anthropic"
            )

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            system_message = None
            claude_messages = []

            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    claude_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })

            params = {
                'model': kwargs.get('model', self.config.model),
                'messages': claude_messages,
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
                'temperature': kwargs.get('temperature', self.config.temperature),
            }

            if system_message:
                params['system'] = system_message

            for key, value in kwargs.items():
                if key not in params and key not in ['model', 'messages', 'max_tokens', 'temperature']:
                    params[key] = value

            response = self._client.messages.create(**params)
            return response.content[0].text

        except ProviderError:
            raise
        except Exception as e:
            # Typed SDK exceptions (#24)
            if _ANTHROPIC_TIMEOUT_ERROR and isinstance(e, _ANTHROPIC_TIMEOUT_ERROR):
                raise ProviderTimeoutError(f"Anthropic request timed out: {e}")
            if _ANTHROPIC_RATE_LIMIT_ERROR and isinstance(e, _ANTHROPIC_RATE_LIMIT_ERROR):
                raise ProviderRateLimitError(f"Anthropic rate limit exceeded: {e}")
            if _ANTHROPIC_API_ERROR and isinstance(e, _ANTHROPIC_API_ERROR):
                raise ProviderAPIError(f"Anthropic API error: {e}")
            # Fallback string matching
            error_msg = str(e).lower()
            if 'timeout' in error_msg:
                raise ProviderTimeoutError(f"Anthropic request timed out: {e}")
            if 'rate limit' in error_msg or '429' in error_msg:
                raise ProviderRateLimitError(f"Anthropic rate limit exceeded: {e}")
            raise ProviderAPIError(f"Anthropic API error: {e}")

    def validate_config(self) -> bool:
        return bool(self.config.api_key and self.config.model)

    def get_provider_name(self) -> str:
        return "anthropic"

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info['supports_streaming'] = True
        info['supports_system_message'] = True
        info['context_window'] = self._get_context_window()
        return info

    def _get_context_window(self) -> int:
        context_windows = {
            'claude-3-5-sonnet-20241022': 200000,
            'claude-3-opus-20240229': 200000,
            'claude-3-sonnet-20240229': 200000,
            'claude-3-haiku-20240307': 200000,
        }
        return context_windows.get(self.config.model, 200000)
