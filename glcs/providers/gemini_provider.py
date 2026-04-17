"""
Google Gemini provider implementation for GLCS.

Supports Gemini 1.5 Pro and Gemini 1.5 Flash.
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
    from google.api_core import exceptions as _google_exceptions
    _GEMINI_DEADLINE_ERROR = _google_exceptions.DeadlineExceeded
    _GEMINI_RATE_LIMIT_ERROR = _google_exceptions.ResourceExhausted
    _GEMINI_API_ERROR = _google_exceptions.GoogleAPICallError
except (ImportError, AttributeError):
    _GEMINI_DEADLINE_ERROR = None
    _GEMINI_RATE_LIMIT_ERROR = None
    _GEMINI_API_ERROR = None


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider

    Supports Gemini models including:
    - gemini-1.5-pro
    - gemini-1.5-flash
    - gemini-pro
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        if not self.config.model:
            self.config.model = "gemini-1.5-flash"

        # Validate config before creating client (#27)
        if not self.config.api_key:
            raise ProviderConfigError(
                "Google API key is required. Set GOOGLE_API_KEY or pass api_key."
            )

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

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            gemini_messages = []
            system_instruction = None

            for msg in messages:
                if msg['role'] == 'system':
                    system_instruction = msg['content']
                else:
                    role = 'model' if msg['role'] == 'assistant' else 'user'
                    gemini_messages.append({
                        'role': role,
                        'parts': [msg['content']]
                    })

            generation_config = {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_output_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            }
            if 'top_p' in kwargs:
                generation_config['top_p'] = kwargs['top_p']
            if 'top_k' in kwargs:
                generation_config['top_k'] = kwargs['top_k']

            # Recreate model only when a system instruction is present (#78 partially —
            # avoids unnecessary recreation on the common no-system-instruction path)
            if system_instruction:
                model = self._genai.GenerativeModel(
                    self.config.model,
                    system_instruction=system_instruction
                )
            else:
                model = self._client

            if len(gemini_messages) > 1:
                history = gemini_messages[:-1]
                current_message = gemini_messages[-1]['parts'][0]
                chat = model.start_chat(history=history)
                response = chat.send_message(
                    current_message,
                    generation_config=generation_config
                )
            else:
                response = model.generate_content(
                    gemini_messages[0]['parts'][0] if gemini_messages else "",
                    generation_config=generation_config
                )

            return response.text

        except ProviderError:
            raise
        except Exception as e:
            # Typed SDK exceptions (#24)
            if _GEMINI_DEADLINE_ERROR and isinstance(e, _GEMINI_DEADLINE_ERROR):
                raise ProviderTimeoutError(f"Gemini request timed out: {e}")
            if _GEMINI_RATE_LIMIT_ERROR and isinstance(e, _GEMINI_RATE_LIMIT_ERROR):
                raise ProviderRateLimitError(f"Gemini rate limit exceeded: {e}")
            if _GEMINI_API_ERROR and isinstance(e, _GEMINI_API_ERROR):
                raise ProviderAPIError(f"Gemini API error: {e}")
            # Fallback string matching
            error_msg = str(e).lower()
            if 'timeout' in error_msg or 'deadline' in error_msg:
                raise ProviderTimeoutError(f"Gemini request timed out: {e}")
            if 'quota' in error_msg or 'rate limit' in error_msg or '429' in error_msg:
                raise ProviderRateLimitError(f"Gemini rate limit exceeded: {e}")
            raise ProviderAPIError(f"Gemini API error: {e}")

    def validate_config(self) -> bool:
        return bool(self.config.api_key and self.config.model)

    def get_provider_name(self) -> str:
        return "gemini"

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info['supports_streaming'] = True
        info['supports_system_instruction'] = True
        info['context_window'] = self._get_context_window()
        return info

    def _get_context_window(self) -> int:
        context_windows = {
            'gemini-1.5-pro': 1000000,
            'gemini-1.5-flash': 1000000,
            'gemini-pro': 32760,
        }
        return context_windows.get(self.config.model, 32760)
