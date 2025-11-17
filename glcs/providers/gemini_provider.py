"""
Google Gemini provider implementation for GLCS.

Supports Gemini 1.5 Pro and Gemini 1.5 Flash.
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


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider

    Supports Gemini models including:
    - gemini-1.5-pro
    - gemini-1.5-flash
    - gemini-pro
    """

    def __init__(self, config: ProviderConfig):
        """Initialize Gemini provider

        Args:
            config: Provider configuration
        """
        super().__init__(config)

        # Set default model if not provided
        if not self.config.model:
            self.config.model = "gemini-1.5-flash"

        # Initialize Gemini client
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.api_key)
            self._genai = genai
            self._client = genai.GenerativeModel(self.config.model)
        except ImportError:
            raise ProviderError(
                "Google Generative AI package not installed. "
                "Install with: pip install google-generativeai"
            )

    def generate(self,
                 messages: List[Dict[str, str]],
                 **kwargs) -> str:
        """Generate response using Google Gemini API

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
            # Convert messages to Gemini format
            # Gemini uses a simpler format with role and parts
            gemini_messages = []
            system_instruction = None

            for msg in messages:
                if msg['role'] == 'system':
                    # Gemini 1.5 supports system instructions
                    system_instruction = msg['content']
                else:
                    # Map roles: assistant -> model, user -> user
                    role = 'model' if msg['role'] == 'assistant' else 'user'
                    gemini_messages.append({
                        'role': role,
                        'parts': [msg['content']]
                    })

            # Create generation config
            generation_config = {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_output_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            }

            # Add any extra generation config parameters
            if 'top_p' in kwargs:
                generation_config['top_p'] = kwargs['top_p']
            if 'top_k' in kwargs:
                generation_config['top_k'] = kwargs['top_k']

            # Recreate model with system instruction if provided
            if system_instruction:
                model = self._genai.GenerativeModel(
                    self.config.model,
                    system_instruction=system_instruction
                )
            else:
                model = self._client

            # Start chat session if we have conversation history
            if len(gemini_messages) > 1:
                # Remove last message (the user's current message)
                history = gemini_messages[:-1]
                current_message = gemini_messages[-1]['parts'][0]

                chat = model.start_chat(history=history)
                response = chat.send_message(
                    current_message,
                    generation_config=generation_config
                )
            else:
                # Single message - use generate_content
                response = model.generate_content(
                    gemini_messages[0]['parts'][0] if gemini_messages else "",
                    generation_config=generation_config
                )

            # Extract and return content
            return response.text

        except Exception as e:
            error_msg = str(e).lower()

            # Check for specific error types
            if 'timeout' in error_msg:
                raise ProviderTimeoutError(f"Gemini request timed out: {e}")
            elif 'quota' in error_msg or 'rate limit' in error_msg or '429' in error_msg:
                raise ProviderRateLimitError(f"Gemini rate limit exceeded: {e}")
            else:
                raise ProviderAPIError(f"Gemini API error: {e}")

    def validate_config(self) -> bool:
        """Validate Gemini configuration

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
            Provider name 'gemini'
        """
        return "gemini"

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information

        Returns:
            Dictionary with model information
        """
        info = super().get_model_info()
        info['supports_streaming'] = True
        info['supports_system_instruction'] = True
        info['context_window'] = self._get_context_window()
        return info

    def _get_context_window(self) -> int:
        """Get context window size for current model

        Returns:
            Context window size in tokens
        """
        context_windows = {
            'gemini-1.5-pro': 1000000,
            'gemini-1.5-flash': 1000000,
            'gemini-pro': 32760,
        }

        return context_windows.get(self.config.model, 32760)
