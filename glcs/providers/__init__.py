"""
LLM Provider abstraction for GLCS.

This module provides a unified interface for multiple LLM providers including
OpenAI, Anthropic Claude, Google Gemini, Groq, and Ollama.
"""

from glcs.providers.base import (
    LLMProvider,
    ProviderConfig,
    ProviderError,
    ProviderConfigError,
    ProviderAPIError,
    ProviderTimeoutError,
    ProviderRateLimitError,
)
from glcs.providers.factory import ProviderFactory

# Import and register providers (lazy import to avoid requiring all dependencies)
def _register_providers():
    """Register all available providers"""

    # Try to import and register OpenAI provider
    try:
        from glcs.providers.openai_provider import OpenAIProvider
        ProviderFactory.register('openai', OpenAIProvider)
    except ImportError:
        pass  # OpenAI not installed

    # Try to import and register Anthropic provider
    try:
        from glcs.providers.anthropic_provider import AnthropicProvider
        ProviderFactory.register('anthropic', AnthropicProvider)
        ProviderFactory.register('claude', AnthropicProvider)  # Alias
    except ImportError:
        pass  # Anthropic not installed

    # Try to import and register Gemini provider
    try:
        from glcs.providers.gemini_provider import GeminiProvider
        ProviderFactory.register('gemini', GeminiProvider)
        ProviderFactory.register('google', GeminiProvider)  # Alias
    except ImportError:
        pass  # Google Generative AI not installed

    # Try to import and register Groq provider
    try:
        from glcs.providers.groq_provider import GroqProvider
        ProviderFactory.register('groq', GroqProvider)
    except ImportError:
        pass  # Groq not installed

    # Try to import and register Ollama provider
    try:
        from glcs.providers.ollama_provider import OllamaProvider
        ProviderFactory.register('ollama', OllamaProvider)
    except ImportError:
        pass  # Ollama not installed


# Auto-register providers on import
_register_providers()

__all__ = [
    'LLMProvider',
    'ProviderConfig',
    'ProviderFactory',
    'ProviderError',
    'ProviderConfigError',
    'ProviderAPIError',
    'ProviderTimeoutError',
    'ProviderRateLimitError',
]
