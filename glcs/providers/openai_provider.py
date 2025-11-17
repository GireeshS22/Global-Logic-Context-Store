"""
OpenAI provider implementation for GLCS.

Supports GPT-4o, GPT-4o-mini, GPT-3.5-turbo, and other OpenAI models.
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


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider

    Supports all OpenAI chat models including:
    - gpt-4o
    - gpt-4o-mini
    - gpt-3.5-turbo
    """

    def __init__(self, config: ProviderConfig):
        """Initialize OpenAI provider

        Args:
            config: Provider configuration
        """
        super().__init__(config)

        # Set default model if not provided
        if not self.config.model:
            self.config.model = "gpt-4o-mini"

        # Initialize OpenAI client
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

    def generate(self,
                 messages: List[Dict[str, str]],
                 **kwargs) -> str:
        """Generate response using OpenAI API

        Args:
            messages: List of messages in OpenAI format
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response

        Raises:
            ProviderAPIError: If API call fails
            ProviderTimeoutError: If request times out
            ProviderRateLimitError: If rate limit is exceeded
        """
        try:
            # Merge config and kwargs
            params = {
                'model': kwargs.get('model', self.config.model),
                'messages': messages,
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            }

            # Add any extra parameters
            for key, value in kwargs.items():
                if key not in params:
                    params[key] = value

            # Make API call
            response = self._client.chat.completions.create(**params)

            # Extract and return content
            return response.choices[0].message.content

        except Exception as e:
            error_msg = str(e).lower()

            # Check for specific error types
            if 'timeout' in error_msg:
                raise ProviderTimeoutError(f"OpenAI request timed out: {e}")
            elif 'rate limit' in error_msg or 'quota' in error_msg:
                raise ProviderRateLimitError(f"OpenAI rate limit exceeded: {e}")
            else:
                raise ProviderAPIError(f"OpenAI API error: {e}")

    def validate_config(self) -> bool:
        """Validate OpenAI configuration

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
            Provider name 'openai'
        """
        return "openai"

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information

        Returns:
            Dictionary with model information
        """
        info = super().get_model_info()
        info['supports_streaming'] = True
        info['supports_functions'] = True
        info['context_window'] = self._get_context_window()
        return info

    def _get_context_window(self) -> int:
        """Get context window size for current model

        Returns:
            Context window size in tokens
        """
        context_windows = {
            'gpt-4o': 128000,
            'gpt-4o-mini': 128000,
            'gpt-4-turbo': 128000,
            'gpt-4': 8192,
            'gpt-3.5-turbo': 16385,
            'gpt-3.5-turbo-16k': 16385,
        }

        return context_windows.get(self.config.model, 4096)
