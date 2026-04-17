"""
Ollama provider implementation for GLCS.

Supports local LLM inference with Ollama (100% private, no API key needed).
"""

import logging
from typing import List, Dict, Any
from glcs.providers.base import (
    LLMProvider,
    ProviderConfig,
    ProviderError,
    ProviderConfigError,
    ProviderAPIError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)

# Import typed SDK exceptions for proper error classification (#24)
try:
    import ollama as _ollama_sdk
    _OLLAMA_RESPONSE_ERROR = _ollama_sdk.ResponseError
except (ImportError, AttributeError):
    _OLLAMA_RESPONSE_ERROR = None


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider

    Supports local models including:
    - llama3.2
    - llama3.1
    - mistral
    - qwen2.5
    - phi3
    - gemma2

    No API key required - runs 100% locally!
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        if not self.config.model:
            self.config.model = "llama3.2"

        self.endpoint = (
            config.extra.get('endpoint', 'http://localhost:11434')
            if config.extra else 'http://localhost:11434'
        )
        # Auto-pull is opt-in — silently downloading multi-GB models in __init__ is
        # dangerous in CI/CD (#26)
        self.auto_pull = (
            config.extra.get('auto_pull', False)
            if config.extra else False
        )

        # Validate model name before connecting (#27)
        if not self.config.model:
            raise ProviderConfigError("Ollama model name is required")

        try:
            import ollama
            self._client = ollama.Client(host=self.endpoint)
            self._ollama = ollama
        except ImportError:
            raise ProviderError(
                "Ollama package not installed. "
                "Install with: pip install ollama"
            )

        self._check_availability()

    def _check_availability(self) -> None:
        """Check if Ollama is running and model is available.

        Raises ProviderError if Ollama is unreachable or the model is missing
        and auto_pull is False.
        """
        try:
            models = self._client.list()
            model_list = (
                models.get('models', []) if isinstance(models, dict)
                else getattr(models, 'models', [])
            )

            available_models = []
            for m in model_list:
                name = (
                    m.get('name') if isinstance(m, dict)
                    else getattr(m, 'model', getattr(m, 'name', None))
                )
                if name:
                    available_models.append(name)

            available_base_models = [name.split(':')[0] for name in available_models]
            model_available = (
                self.config.model in available_models
                or self.config.model.split(':')[0] in available_base_models
            )

            if not model_available:
                if self.auto_pull:
                    logger.info(
                        "Model '%s' not found locally. Pulling from registry...",
                        self.config.model
                    )
                    try:
                        self._client.pull(self.config.model)
                        logger.info("Successfully pulled model '%s'", self.config.model)
                    except Exception as pull_error:
                        raise ProviderError(
                            f"Model '{self.config.model}' not available and could not be pulled. "
                            f"Error: {pull_error}\n"
                            f"Available models: {', '.join(available_models)}\n"
                            f"Pull manually with: ollama pull {self.config.model}"
                        )
                else:
                    raise ProviderError(
                        f"Model '{self.config.model}' is not available locally.\n"
                        f"Available models: {', '.join(available_models) or 'none'}\n"
                        f"Pull it with: ollama pull {self.config.model}\n"
                        f"Or set auto_pull=True in extra config to allow automatic downloads."
                    )

        except ProviderError:
            raise
        except Exception as e:
            if 'connection' in str(e).lower() or 'refused' in str(e).lower():
                raise ProviderError(
                    f"Cannot connect to Ollama at {self.endpoint}. "
                    "Make sure Ollama is running: ollama serve"
                )
            raise ProviderError(f"Error checking Ollama availability: {e}")

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            params = {
                'model': kwargs.get('model', self.config.model),
                'messages': messages,
            }
            options = {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'num_predict': kwargs.get('max_tokens', self.config.max_tokens),
            }
            if 'top_p' in kwargs:
                options['top_p'] = kwargs['top_p']
            if 'top_k' in kwargs:
                options['top_k'] = kwargs['top_k']
            params['options'] = options

            response = self._client.chat(**params)
            return response['message']['content']

        except ProviderError:
            raise
        except Exception as e:
            # Typed SDK exception (#24)
            if _OLLAMA_RESPONSE_ERROR and isinstance(e, _OLLAMA_RESPONSE_ERROR):
                raise ProviderAPIError(f"Ollama API error (status {e.status_code}): {e}")
            # Fallback string matching
            error_msg = str(e).lower()
            if 'timeout' in error_msg:
                raise ProviderTimeoutError(f"Ollama request timed out: {e}")
            if 'connection' in error_msg or 'refused' in error_msg:
                raise ProviderAPIError(
                    f"Cannot connect to Ollama. Is it running? Error: {e}"
                )
            raise ProviderAPIError(f"Ollama error: {e}")

    def validate_config(self) -> bool:
        return bool(self.config.model)

    def get_provider_name(self) -> str:
        return "ollama"

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info['local'] = True
        info['requires_api_key'] = False
        info['endpoint'] = self.endpoint
        info['privacy'] = '100% local - no data leaves your machine'

        try:
            model_info = self._client.show(self.config.model)
            info['model_details'] = model_info
        except Exception:  # #30: bare except → except Exception
            pass

        return info

    def list_local_models(self) -> List[str]:
        try:
            models = self._client.list()
            model_list = (
                models.get('models', []) if isinstance(models, dict)
                else getattr(models, 'models', [])
            )
            available_models = []
            for m in model_list:
                name = (
                    m.get('name') if isinstance(m, dict)
                    else getattr(m, 'model', getattr(m, 'name', None))
                )
                if name:
                    available_models.append(name)
            return available_models
        except Exception as e:
            raise ProviderAPIError(f"Error listing Ollama models: {e}")

    def pull_model(self, model_name: str) -> None:
        """Pull a model from the Ollama registry.

        Args:
            model_name: Name of model to pull

        Raises:
            ProviderAPIError: If pull fails
        """
        try:
            logger.info("Pulling model '%s'...", model_name)  # #29: print → logger
            self._client.pull(model_name)
            logger.info("Successfully pulled model '%s'", model_name)  # #29
        except Exception as e:
            raise ProviderAPIError(f"Error pulling model '{model_name}': {e}")
