"""
Groq provider implementation for GLCS.

Supports fast inference with Mixtral, Llama, and other models.
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


class GroqProvider(LLMProvider):
    """Groq LLM provider

    Groq provides ultra-fast inference for open-source models:
    - mixtral-8x7b-32768
    - llama-3.1-70b-versatile
    - llama-3.1-8b-instant
    - gemma-7b-it
    """

    def __init__(self, config: ProviderConfig):
        """Initialize Groq provider

        Args:
            config: Provider configuration
        """
        super().__init__(config)

        # Set default model if not provided
        if not self.config.model:
            self.config.model = "mixtral-8x7b-32768"

        # Initialize Groq client
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

    def generate(self,
                 messages: List[Dict[str, str]],
                 **kwargs) -> str:
        """Generate response using Groq API

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
            # Groq uses OpenAI-compatible API
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
                raise ProviderTimeoutError(f"Groq request timed out: {e}")
            elif 'rate limit' in error_msg or 'quota' in error_msg or '429' in error_msg:
                raise ProviderRateLimitError(f"Groq rate limit exceeded: {e}")
            else:
                raise ProviderAPIError(f"Groq API error: {e}")

    def validate_config(self) -> bool:
        """Validate Groq configuration

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
            Provider name 'groq'
        """
        return "groq"

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information

        Returns:
            Dictionary with model information
        """
        info = super().get_model_info()
        info['supports_streaming'] = True
        info['ultra_fast'] = True
        info['context_window'] = self._get_context_window()
        return info

    def _get_context_window(self) -> int:
        """Get context window size for current model

        Returns:
            Context window size in tokens
        """
        context_windows = {
            'mixtral-8x7b-32768': 32768,
            'llama-3.1-70b-versatile': 131072,
            'llama-3.1-8b-instant': 131072,
            'gemma-7b-it': 8192,
            'llama3-70b-8192': 8192,
            'llama3-8b-8192': 8192,
        }

        return context_windows.get(self.config.model, 8192)
