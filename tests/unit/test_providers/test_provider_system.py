"""
Test suite for the provider system.

Tests provider abstraction, factory, and all provider implementations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from glcs.providers import (
    LLMProvider,
    ProviderConfig,
    ProviderFactory,
    ProviderError,
    ProviderConfigError,
)


class TestProviderConfig:
    """Test ProviderConfig dataclass"""

    def test_provider_config_creation(self):
        """Test creating provider config"""
        config = ProviderConfig(
            api_key="test-key",
            model="test-model",
            temperature=0.5,
            max_tokens=100
        )

        assert config.api_key == "test-key"
        assert config.model == "test-model"
        assert config.temperature == 0.5
        assert config.max_tokens == 100

    def test_provider_config_defaults(self):
        """Test provider config defaults"""
        config = ProviderConfig()

        assert config.api_key is None
        assert config.model == ""
        assert config.temperature == 0.7
        assert config.max_tokens == 150
        assert config.timeout == 30
        assert config.extra == {}


class TestProviderFactory:
    """Test ProviderFactory"""

    def setup_method(self):
        """Setup test fixtures"""
        # Create a mock provider for testing
        class MockProvider(LLMProvider):
            def generate(self, messages, **kwargs):
                return "mock response"

            def validate_config(self):
                return bool(self.config.api_key)

            def get_provider_name(self):
                return "mock"

        self.MockProvider = MockProvider

    def test_register_provider(self):
        """Test registering a provider"""
        # Clear factory first
        ProviderFactory.clear()

        ProviderFactory.register('mock', self.MockProvider)
        assert ProviderFactory.is_registered('mock')

    def test_register_duplicate_provider(self):
        """Test registering duplicate provider raises error"""
        ProviderFactory.clear()
        ProviderFactory.register('mock', self.MockProvider)

        with pytest.raises(ValueError, match="already registered"):
            ProviderFactory.register('mock', self.MockProvider)

    def test_create_provider(self):
        """Test creating a provider"""
        ProviderFactory.clear()
        ProviderFactory.register('mock', self.MockProvider)

        config = ProviderConfig(api_key="test-key", model="test-model")
        provider = ProviderFactory.create('mock', config=config)

        assert isinstance(provider, self.MockProvider)
        assert provider.get_provider_name() == "mock"

    def test_create_unknown_provider(self):
        """Test creating unknown provider raises error"""
        ProviderFactory.clear()

        with pytest.raises(ProviderConfigError, match="Unknown provider"):
            ProviderFactory.create('unknown_provider')

    def test_list_providers(self):
        """Test listing registered providers"""
        ProviderFactory.clear()
        ProviderFactory.register('mock1', self.MockProvider)
        ProviderFactory.register('mock2', self.MockProvider)

        providers = ProviderFactory.list_providers()
        assert 'mock1' in providers
        assert 'mock2' in providers

    def test_unregister_provider(self):
        """Test unregistering a provider"""
        ProviderFactory.clear()
        ProviderFactory.register('mock', self.MockProvider)

        ProviderFactory.unregister('mock')
        assert not ProviderFactory.is_registered('mock')


@pytest.mark.requires_api_key
class TestOpenAIProvider:
    """Test OpenAI provider (requires API key)"""

    def test_openai_provider_import(self):
        """Test importing OpenAI provider"""
        try:
            from glcs.providers.openai_provider import OpenAIProvider
            assert OpenAIProvider is not None
        except (ImportError, ProviderError):
            pytest.skip("OpenAI not installed")

    def test_openai_provider_creation(self):
        """Test creating OpenAI provider"""
        try:
            from glcs.providers.openai_provider import OpenAIProvider

            config = ProviderConfig(api_key="test-key", model="gpt-4o-mini")
            provider = OpenAIProvider(config)

            assert provider.get_provider_name() == "openai"
            assert provider.config.model == "gpt-4o-mini"
        except (ImportError, ProviderError):
            pytest.skip("OpenAI not installed")

    def test_openai_provider_validation(self):
        """Test OpenAI provider validation"""
        try:
            from glcs.providers.openai_provider import OpenAIProvider

            # Valid config
            config = ProviderConfig(api_key="test-key", model="gpt-4o-mini")
            provider = OpenAIProvider(config)
            assert provider.validate_config() is True

            # Invalid config (no API key)
            with pytest.raises(ProviderError):
                config = ProviderConfig(model="gpt-4o-mini")
                provider = OpenAIProvider(config)
        except (ImportError, ProviderError) as e:
            if "not installed" in str(e):
                pytest.skip("OpenAI not installed")
            raise


@pytest.mark.requires_api_key
class TestAnthropicProvider:
    """Test Anthropic provider (requires API key)"""

    def test_anthropic_provider_import(self):
        """Test importing Anthropic provider"""
        try:
            from glcs.providers.anthropic_provider import AnthropicProvider
            assert AnthropicProvider is not None
        except (ImportError, ProviderError):
            pytest.skip("Anthropic not installed")

    def test_anthropic_provider_creation(self):
        """Test creating Anthropic provider"""
        try:
            from glcs.providers.anthropic_provider import AnthropicProvider

            config = ProviderConfig(api_key="test-key", model="claude-3-5-sonnet-20241022")
            provider = AnthropicProvider(config)

            assert provider.get_provider_name() == "anthropic"
            assert provider.config.model == "claude-3-5-sonnet-20241022"
        except (ImportError, ProviderError):
            pytest.skip("Anthropic not installed")


@pytest.mark.requires_api_key
class TestGeminiProvider:
    """Test Gemini provider (requires API key)"""

    def test_gemini_provider_import(self):
        """Test importing Gemini provider"""
        try:
            from glcs.providers.gemini_provider import GeminiProvider
            assert GeminiProvider is not None
        except (ImportError, ProviderError):
            pytest.skip("Google Generative AI not installed")

    def test_gemini_provider_creation(self):
        """Test creating Gemini provider"""
        try:
            from glcs.providers.gemini_provider import GeminiProvider

            config = ProviderConfig(api_key="test-key", model="gemini-1.5-flash")
            provider = GeminiProvider(config)

            assert provider.get_provider_name() == "gemini"
            assert provider.config.model == "gemini-1.5-flash"
        except (ImportError, ProviderError):
            pytest.skip("Google Generative AI not installed")

    def test_gemini_model_caching(self):
        """Test that Gemini provider caches model instances (#78)"""
        try:
            from glcs.providers.gemini_provider import GeminiProvider
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model_instance = mock_model_class.return_value
                mock_model_instance.generate_content.return_value = MagicMock(text="Response")
                
                config = ProviderConfig(api_key="test-key", model="gemini-1.5-flash")
                provider = GeminiProvider(config)
                
                messages = [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "Hello"}
                ]
                
                # First call
                provider.generate(messages)
                # Second call with same system instruction
                provider.generate(messages)
                
                # Should have created the system-instruction model exactly once
                # (Plus once in __init__ for the base client)
                assert mock_model_class.call_count == 2
                
                # Third call with different instruction
                messages2 = [{"role": "system", "content": "New prompt"}, {"role": "user", "content": "Hi"}]
                provider.generate(messages2)
                assert mock_model_class.call_count == 3
                
        except (ImportError, ProviderError):
            pytest.skip("Google Generative AI not installed")


@pytest.mark.requires_api_key
class TestGroqProvider:
    """Test Groq provider (requires API key)"""

    def test_groq_provider_import(self):
        """Test importing Groq provider"""
        try:
            from glcs.providers.groq_provider import GroqProvider
            assert GroqProvider is not None
        except (ImportError, ProviderError):
            pytest.skip("Groq not installed")

    def test_groq_provider_creation(self):
        """Test creating Groq provider"""
        try:
            from glcs.providers.groq_provider import GroqProvider

            config = ProviderConfig(api_key="test-key", model="mixtral-8x7b-32768")
            provider = GroqProvider(config)

            assert provider.get_provider_name() == "groq"
            assert provider.config.model == "mixtral-8x7b-32768"
        except (ImportError, ProviderError):
            pytest.skip("Groq not installed")


class TestOllamaProvider:
    """Test Ollama provider (local, no API key needed)"""

    def test_ollama_provider_import(self):
        """Test importing Ollama provider"""
        try:
            from glcs.providers.ollama_provider import OllamaProvider
            assert OllamaProvider is not None
        except (ImportError, ProviderError):
            pytest.skip("Ollama not installed")

    @pytest.mark.slow
    def test_ollama_provider_validation(self):
        """Test Ollama provider validation"""
        try:
            from glcs.providers.ollama_provider import OllamaProvider

            config = ProviderConfig(model="llama3.2")
            config.extra = {'endpoint': 'http://localhost:11434'}

            # Note: This will fail if Ollama is not running, which is expected
            try:
                provider = OllamaProvider(config)
                assert provider.validate_config() is True
                assert provider.get_provider_name() == "ollama"
            except ProviderError:
                # Expected if Ollama is not running
                pytest.skip("Ollama not running")
        except (ImportError, ProviderError):
            pytest.skip("Ollama not installed")


class TestProviderIntegration:
    """Integration tests for provider system"""

    def test_provider_auto_registration(self):
        """Test that providers are auto-registered on import"""
        from glcs.providers import ProviderFactory
        from glcs.providers import _register_providers
        
        # Re-register because previous tests might have cleared the factory
        _register_providers()

        # Check if at least some providers are registered
        providers = ProviderFactory.list_providers()
        assert len(providers) > 0

    def test_create_provider(self):
        """Test creating a provider via factory"""
        from glcs.providers import ProviderFactory, ProviderConfig

        # Try to create OpenAI provider if available
        if ProviderFactory.is_registered('openai'):
            try:
                import openai
                config = ProviderConfig(api_key="test-key", model="gpt-4o-mini")
                provider = ProviderFactory.create('openai', config=config)
                assert provider.get_provider_name() == "openai"
            except ImportError:
                pytest.skip("openai package not installed")
            except Exception as e:
                pytest.fail(f"Failed to create openai provider: {e}")


    def test_multiple_providers_coexist(self):
        """Test multiple providers can coexist"""
        from glcs.providers import ProviderFactory, ProviderConfig
        import importlib

        providers = ProviderFactory.list_providers()
        assert len(providers) >= 1

        # Create all available providers
        for provider_name in providers:
            config = ProviderConfig(api_key="test-key", model="test-model")
            if provider_name == 'ollama':
                config.extra = {'endpoint': 'http://localhost:11434'}

            # Check if dependencies are installed before trying to create
            if provider_name == 'openai':
                try:
                    importlib.import_module('openai')
                except ImportError:
                    continue
            elif provider_name == 'anthropic':
                try:
                    importlib.import_module('anthropic')
                except ImportError:
                    continue
            elif provider_name == 'gemini':
                try:
                    importlib.import_module('google.generativeai')
                except ImportError:
                    continue
            elif provider_name == 'groq':
                try:
                    importlib.import_module('groq')
                except ImportError:
                    continue

            try:
                provider = ProviderFactory.create(provider_name, config=config)
                assert provider is not None
                
                # Normalize provider name for comparison (handle aliases)
                actual_name = provider.get_provider_name()
                if provider_name in ['anthropic', 'claude']:
                    assert actual_name == 'anthropic'
                elif provider_name in ['gemini', 'google']:
                    assert actual_name == 'gemini'
                else:
                    assert actual_name == provider_name
            except (ProviderError, ProviderConfigError, ImportError) as e:
                # Log and skip if it's a known environment issue
                print(f"Skipping provider {provider_name} due to environment/config: {e}")
                continue
