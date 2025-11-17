"""
Ollama provider implementation for GLCS.

Supports local LLM inference with Ollama (100% private, no API key needed).
"""

from typing import List, Dict, Any, Optional
from glcs.providers.base import (
    LLMProvider,
    ProviderConfig,
    ProviderError,
    ProviderAPIError,
    ProviderTimeoutError,
)


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
        """Initialize Ollama provider

        Args:
            config: Provider configuration
        """
        super().__init__(config)

        # Set default model if not provided
        if not self.config.model:
            self.config.model = "llama3.2"

        # Get endpoint from config or use default
        self.endpoint = config.extra.get('endpoint', 'http://localhost:11434') if config.extra else 'http://localhost:11434'

        # Initialize Ollama client
        try:
            import ollama
            self._client = ollama.Client(host=self.endpoint)
            self._ollama = ollama
        except ImportError:
            raise ProviderError(
                "Ollama package not installed. "
                "Install with: pip install ollama"
            )

        # Check if Ollama is running and model is available
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if Ollama is running and model is available

        Raises:
            ProviderError: If Ollama is not available
        """
        try:
            # Try to list models to check if Ollama is running
            models = self._client.list()

            # Check if our model is available
            available_models = [m['name'].split(':')[0] for m in models.get('models', [])]

            if self.config.model not in available_models:
                # Model not available - try to pull it
                print(f"Model '{self.config.model}' not found locally. Attempting to pull...")
                try:
                    self._client.pull(self.config.model)
                    print(f"Successfully pulled model '{self.config.model}'")
                except Exception as pull_error:
                    raise ProviderError(
                        f"Model '{self.config.model}' not available and could not be pulled. "
                        f"Error: {pull_error}\n"
                        f"Available models: {', '.join(available_models)}\n"
                        f"Pull manually with: ollama pull {self.config.model}"
                    )

        except Exception as e:
            if 'connection' in str(e).lower() or 'refused' in str(e).lower():
                raise ProviderError(
                    f"Cannot connect to Ollama at {self.endpoint}. "
                    "Make sure Ollama is running. "
                    "Start with: ollama serve"
                )
            # Re-raise if it's already a ProviderError
            if isinstance(e, ProviderError):
                raise
            # Otherwise wrap it
            raise ProviderError(f"Error checking Ollama availability: {e}")

    def generate(self,
                 messages: List[Dict[str, str]],
                 **kwargs) -> str:
        """Generate response using Ollama

        Args:
            messages: List of messages in OpenAI format
            **kwargs: Additional parameters

        Returns:
            Generated text response

        Raises:
            ProviderAPIError: If generation fails
            ProviderTimeoutError: If request times out
        """
        try:
            # Ollama uses similar message format to OpenAI
            params = {
                'model': kwargs.get('model', self.config.model),
                'messages': messages,
            }

            # Add generation options
            options = {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'num_predict': kwargs.get('max_tokens', self.config.max_tokens),
            }

            # Add any extra options
            if 'top_p' in kwargs:
                options['top_p'] = kwargs['top_p']
            if 'top_k' in kwargs:
                options['top_k'] = kwargs['top_k']

            params['options'] = options

            # Make API call
            response = self._client.chat(**params)

            # Extract and return content
            return response['message']['content']

        except Exception as e:
            error_msg = str(e).lower()

            # Check for specific error types
            if 'timeout' in error_msg:
                raise ProviderTimeoutError(f"Ollama request timed out: {e}")
            elif 'connection' in error_msg or 'refused' in error_msg:
                raise ProviderAPIError(
                    f"Cannot connect to Ollama. Is it running? Error: {e}"
                )
            else:
                raise ProviderAPIError(f"Ollama error: {e}")

    def validate_config(self) -> bool:
        """Validate Ollama configuration

        Returns:
            True if configuration is valid
        """
        # No API key needed for Ollama
        # Just check model
        if not self.config.model:
            return False

        return True

    def get_provider_name(self) -> str:
        """Get provider name

        Returns:
            Provider name 'ollama'
        """
        return "ollama"

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information

        Returns:
            Dictionary with model information
        """
        info = super().get_model_info()
        info['local'] = True
        info['requires_api_key'] = False
        info['endpoint'] = self.endpoint
        info['privacy'] = '100% local - no data leaves your machine'

        try:
            # Get model details from Ollama
            model_info = self._client.show(self.config.model)
            info['model_details'] = model_info
        except:
            pass

        return info

    def list_local_models(self) -> List[str]:
        """List locally available models

        Returns:
            List of model names
        """
        try:
            models = self._client.list()
            return [m['name'] for m in models.get('models', [])]
        except Exception as e:
            raise ProviderAPIError(f"Error listing Ollama models: {e}")

    def pull_model(self, model_name: str) -> None:
        """Pull a model from Ollama registry

        Args:
            model_name: Name of model to pull

        Raises:
            ProviderAPIError: If pull fails
        """
        try:
            print(f"Pulling model '{model_name}'...")
            self._client.pull(model_name)
            print(f"Successfully pulled model '{model_name}'")
        except Exception as e:
            raise ProviderAPIError(f"Error pulling model '{model_name}': {e}")
