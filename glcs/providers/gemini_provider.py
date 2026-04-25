"""
Google Gemini provider implementation for GLCS.

Uses the google-genai SDK (google.generativeai is deprecated).
Supports Gemini 2.0 Flash, Gemini 2.5 Flash, and other current models.
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


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider (google-genai SDK).

    Supports current Gemini models including:
    - gemini-2.0-flash
    - gemini-2.5-flash-preview-05-20
    - gemini-2.5-pro-preview-05-06
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        if not self.config.model:
            self.config.model = "gemini-2.5-flash"

        if not self.config.api_key:
            raise ProviderConfigError(
                "Google API key is required. Set GOOGLE_API_KEY or pass api_key."
            )

        try:
            from google import genai
            self._client = genai.Client(api_key=self.config.api_key)
            self._genai = genai
        except ImportError:
            raise ProviderError(
                "google-genai package not installed. "
                "Install with: pip install google-genai"
            )

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            from google.genai import types

            system_instruction = None
            contents = []

            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                else:
                    role = "model" if msg["role"] == "assistant" else "user"
                    contents.append(
                        types.Content(
                            role=role,
                            parts=[types.Part(text=msg["content"])],
                        )
                    )

            config_kwargs: Dict[str, Any] = {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_output_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            }
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction

            generate_config = types.GenerateContentConfig(**config_kwargs)

            response = self._client.models.generate_content(
                model=kwargs.get("model", self.config.model),
                contents=contents,
                config=generate_config,
            )
            return response.text

        except ProviderError:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg or "deadline" in error_msg:
                raise ProviderTimeoutError(f"Gemini request timed out: {e}")
            if "quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                raise ProviderRateLimitError(f"Gemini rate limit exceeded: {e}")
            raise ProviderAPIError(f"Gemini API error: {e}")

    def validate_config(self) -> bool:
        return bool(self.config.api_key and self.config.model)

    def get_provider_name(self) -> str:
        return "gemini"

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info["supports_streaming"] = True
        info["supports_system_instruction"] = True
        info["context_window"] = self._get_context_window()
        return info

    def _get_context_window(self) -> int:
        context_windows = {
            "gemini-2.0-flash": 1048576,
            "gemini-2.5-flash-preview-05-20": 1048576,
            "gemini-2.5-pro-preview-05-06": 1048576,
            "gemini-1.5-pro": 1048576,
            "gemini-1.5-flash": 1048576,
        }
        return context_windows.get(self.config.model, 1048576)
