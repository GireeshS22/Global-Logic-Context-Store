"""
Anthropic Claude provider implementation for GLCS.

Supports Claude 3.5 Sonnet, Claude 3 Opus, and Claude 3 Haiku.
"""

from typing import List, Dict, Any, Optional
from glcs.providers.base import (
    LLMProvider,
    ProviderConfig,
    ProviderError,
    ProviderAPIError,
    ProviderTimeoutError,
    ProviderRateLimitError,
)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider

    Supports all Claude 3.x models including:
    - claude-3-5-sonnet-20241022
    - claude-3-opus-20240229
    - claude-3-sonnet-20240229
    - claude-3-haiku-20240307
    """

    def __init__(self, config: ProviderConfig):
        """Initialize Anthropic provider

        Args:
            config: Provider configuration
        """
        super().__init__(config)

        # Set default model if not provided
        if not self.config.model:
            self.config.model = "claude-3-5-sonnet-20241022"

        # Initialize Anthropic client
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

    def generate(self,
                 messages: List[Dict[str, str]],
                 **kwargs) -> str:
        """Generate response using Anthropic Claude API

        Args:
            messages: List of messages in OpenAI format
            **kwargs: Additional parameters

        Returns:
            Generated text response

        Raises:
            ProviderAPIError: If API call fails
            ProviderTimeoutError: If request times out
            ProviderRateLimitError: If rate limit is exceeded
        """
        try:
            # Convert messages to Anthropic format
            system_message = None
            claude_messages = []

            for msg in messages:
                if msg['role'] == 'system':
                    # Claude uses separate system parameter
                    system_message = msg['content']
                else:
                    claude_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })

            # Merge config and kwargs
            params = {
                'model': kwargs.get('model', self.config.model),
                'messages': claude_messages,
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
                'temperature': kwargs.get('temperature', self.config.temperature),
            }

            # Add system message if present
            if system_message:
                params['system'] = system_message

            # Add any extra parameters
            for key, value in kwargs.items():
                if key not in params and key not in ['model', 'messages', 'max_tokens', 'temperature']:
                    params[key] = value

            # Make API call
            response = self._client.messages.create(**params)

            # Extract and return content
            return response.content[0].text

        except Exception as e:
            error_msg = str(e).lower()

            # Check for specific error types
            if 'timeout' in error_msg:
                raise ProviderTimeoutError(f"Anthropic request timed out: {e}")
            elif 'rate limit' in error_msg or '429' in error_msg:
                raise ProviderRateLimitError(f"Anthropic rate limit exceeded: {e}")
            else:
                raise ProviderAPIError(f"Anthropic API error: {e}")

    def validate_config(self) -> bool:
        """Validate Anthropic configuration

        Returns:
            True if configuration is valid
        """
        # Check API key
        if not self.config.api_key:
            return False

        # Check model
        if not self.config.model:
            return False

        return True

    def get_provider_name(self) -> str:
        """Get provider name

        Returns:
            Provider name 'anthropic'
        """
        return "anthropic"

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information

        Returns:
            Dictionary with model information
        """
        info = super().get_model_info()
        info['supports_streaming'] = True
        info['supports_system_message'] = True
        info['context_window'] = self._get_context_window()
        return info

    def _get_context_window(self) -> int:
        """Get context window size for current model

        Returns:
            Context window size in tokens
        """
        context_windows = {
            'claude-3-5-sonnet-20241022': 200000,
            'claude-3-opus-20240229': 200000,
            'claude-3-sonnet-20240229': 200000,
            'claude-3-haiku-20240307': 200000,
        }

        return context_windows.get(self.config.model, 200000)
