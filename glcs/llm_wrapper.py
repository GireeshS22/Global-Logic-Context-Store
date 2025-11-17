"""
LLM API wrapper with GLCS consistency checking.

Supports multiple providers: OpenAI, Anthropic Claude, Google Gemini, Groq, and Ollama.
"""

import os
from typing import Optional, Dict, Any, List, Tuple, Union
from dotenv import load_dotenv
from glcs.parser import SimpleParser
from glcs.memory import SimpleMemory
from glcs.checker import ConsistencyChecker
from glcs.core import LogicalStatement, LogicalType
from glcs.providers import (
    LLMProvider,
    ProviderConfig,
    ProviderFactory,
    ProviderError,
)
from glcs.config import get_config

# Load environment variables
load_dotenv()


class GLCSWrapper:
    """Wrapper for LLM APIs with GLCS consistency checking

    This wrapper integrates GLCS with multiple LLM providers to provide
    consistency checking for both prompts and responses.

    Supports: OpenAI, Anthropic Claude, Google Gemini, Groq, and Ollama.
    """

    def __init__(
        self,
        provider: Optional[Union[str, LLMProvider]] = None,
        api_key: Optional[str] = None,  # Backward compatibility
        model: Optional[str] = None,
        memory_path: Optional[str] = None,
        config_path: Optional[str] = None,
        **provider_kwargs
    ):
        """Initialize the GLCS wrapper

        Args:
            provider: Provider name ('openai', 'anthropic', 'gemini', 'groq', 'ollama')
                     or LLMProvider instance. If None, uses default from config.
            api_key: API key (backward compatibility with stage 1.3, implies OpenAI)
            model: Model name (optional override)
            memory_path: Path for memory persistence
            config_path: Path to config file (optional)
            **provider_kwargs: Additional provider configuration

        Examples:
            # New way (recommended)
            wrapper = GLCSWrapper(provider='openai')
            wrapper = GLCSWrapper(provider='claude')
            wrapper = GLCSWrapper(provider='ollama')

            # Old way (backward compatibility)
            wrapper = GLCSWrapper(api_key='sk-...', model='gpt-3.5-turbo')

            # With custom config
            wrapper = GLCSWrapper(provider='anthropic', model='claude-3-opus')
        """
        # Load configuration
        self.config = get_config(config_path)

        # Determine provider
        if isinstance(provider, LLMProvider):
            # Direct provider instance provided
            self.provider = provider
            self.provider_name = provider.get_provider_name()
        elif isinstance(provider, str):
            # Provider name provided
            self.provider_name = provider
            self.provider = self._create_provider(provider, api_key, model, **provider_kwargs)
        elif api_key:
            # Backward compatibility: api_key provided implies OpenAI
            self.provider_name = 'openai'
            self.provider = self._create_provider('openai', api_key, model, **provider_kwargs)
        else:
            # No provider specified, use default from config
            self.provider_name = self.config.get_default_provider()
            self.provider = self._create_provider(self.provider_name, api_key, model, **provider_kwargs)

        # Initialize GLCS components
        self.parser = SimpleParser()
        memory_path = memory_path or self.config.get_memory_config().get('persist_path')
        self.memory = SimpleMemory(persist_path=memory_path)
        self.checker = ConsistencyChecker(self.memory)

        # Conversation history
        self.history: List[Dict[str, str]] = []

    def _create_provider(
        self,
        provider_name: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """Create provider instance

        Args:
            provider_name: Provider name
            api_key: API key (optional)
            model: Model name (optional)
            **kwargs: Additional configuration

        Returns:
            Provider instance

        Raises:
            ProviderError: If provider cannot be created
        """
        try:
            # Get provider config from file
            provider_config_dict = self.config.get_provider_config(provider_name)

            # Override with provided values
            if api_key:
                provider_config_dict['api_key'] = api_key
            if model:
                provider_config_dict['model'] = model

            # Merge additional kwargs
            for key, value in kwargs.items():
                if key not in ['provider', 'memory_path', 'config_path']:
                    provider_config_dict[key] = value

            # Handle Ollama endpoint
            if provider_name == 'ollama' and 'endpoint' in provider_config_dict:
                if 'extra' not in provider_config_dict:
                    provider_config_dict['extra'] = {}
                provider_config_dict['extra']['endpoint'] = provider_config_dict.pop('endpoint')

            # Create ProviderConfig
            config = ProviderConfig(**provider_config_dict)

            # Create provider
            provider = ProviderFactory.create(provider_name, config=config)

            return provider

        except Exception as e:
            raise ProviderError(f"Failed to create provider '{provider_name}': {e}")

    def check_and_store(self, text: str) -> Tuple[bool, List[str]]:
        """Check consistency and store if valid

        Args:
            text: Text to check and potentially store

        Returns:
            Tuple of (all_consistent, violations)
        """
        statements = self.parser.extract_statements(text)
        all_consistent = True
        all_violations = []

        for stmt in statements:
            is_consistent, confidence, violations = self.checker.check_consistency(stmt)

            if is_consistent:
                # Store the statement
                success = self.memory.store(stmt)
                if not success:
                    all_consistent = False
                    all_violations.append(f"Failed to store: {stmt.raw_text}")
            else:
                all_consistent = False
                all_violations.extend(violations)

        return all_consistent, all_violations

    def _build_context(self, max_facts: int = 10) -> str:
        """Build context from stored knowledge

        Args:
            max_facts: Maximum number of facts to include

        Returns:
            Formatted context string
        """
        context_parts = []

        # Get recent facts from memory
        stats = self.memory.get_stats()
        if stats['total'] > 0:
            context_parts.append("Known facts:")

            # Get some universal rules
            universals = self.memory.query(type=LogicalType.UNIVERSAL)
            for stmt in universals[:3]:  # Include up to 3 universal rules
                context_parts.append(f"- {stmt.raw_text}")

            # Get some ground facts
            grounds = self.memory.query(type=LogicalType.GROUND)
            for stmt in grounds[:max(0, max_facts - 3)]:
                context_parts.append(f"- {stmt.raw_text}")

        return "\n".join(context_parts) if context_parts else ""

    def generate(
        self,
        prompt: str,
        check_consistency: bool = True,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response with optional consistency checking

        Args:
            prompt: User prompt
            check_consistency: Whether to check consistency
            max_tokens: Maximum tokens in response (optional)
            temperature: Sampling temperature (optional)
            **kwargs: Additional provider-specific parameters

        Returns:
            Dictionary with response and metadata
        """
        result = {
            'prompt': prompt,
            'response': '',
            'consistent': True,
            'violations': [],
            'stored_facts': 0,
            'provider': self.provider_name,
        }

        # Check prompt consistency
        if check_consistency:
            prompt_consistent, prompt_violations = self.check_and_store(prompt)
            result['consistent'] = prompt_consistent
            result['violations'].extend(prompt_violations)

        # Build context from memory
        context = self._build_context()

        # Augment prompt with context if available
        if context:
            augmented_prompt = (
                f"{context}\n\n"
                f"User: {prompt}\n\n"
                f"Please respond while respecting the known facts above."
            )
        else:
            augmented_prompt = prompt

        # Add to history
        self.history.append({"role": "user", "content": prompt})

        # Prepare messages
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Be logically consistent and respect established facts."
            },
            *self.history[-10:],  # Include last 10 messages for context
        ]

        # Generate response
        try:
            # Prepare kwargs for provider
            gen_kwargs = {}
            if max_tokens is not None:
                gen_kwargs['max_tokens'] = max_tokens
            if temperature is not None:
                gen_kwargs['temperature'] = temperature
            gen_kwargs.update(kwargs)

            response_text = self.provider.generate(messages, **gen_kwargs)
            result['response'] = response_text

            # Add to history
            self.history.append({"role": "assistant", "content": response_text})

            # Check response consistency
            if check_consistency:
                response_consistent, response_violations = self.check_and_store(response_text)

                # If response is inconsistent, note it but still return it
                if not response_consistent:
                    result['consistent'] = False
                    result['violations'].extend(response_violations)

        except Exception as e:
            result['response'] = f"Error generating response: {str(e)}"
            result['consistent'] = False
            result['violations'].append(str(e))

        # Add statistics
        result['memory_stats'] = self.memory.get_stats()

        return result

    def verify_statement(self, statement: str) -> Dict[str, Any]:
        """Verify a statement against stored knowledge

        Args:
            statement: Statement to verify

        Returns:
            Dictionary with verification results
        """
        result = {
            'statement': statement,
            'parsed': False,
            'consistent': True,
            'confidence': 0.0,
            'violations': [],
            'supporting_facts': []
        }

        # Try to parse the statement
        parsed = self.parser.parse(statement)
        if not parsed:
            result['parsed'] = False
            result['violations'].append("Could not parse statement into logical form")
            return result

        result['parsed'] = True

        # Check consistency
        is_consistent, confidence, violations = self.checker.check_consistency(parsed)
        result['consistent'] = is_consistent
        result['confidence'] = confidence
        result['violations'] = violations

        # Get supporting facts
        supporting = self.checker.get_supporting_facts(parsed)
        result['supporting_facts'] = [s.raw_text for s in supporting]

        return result

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of stored knowledge

        Returns:
            Dictionary with memory statistics and samples
        """
        stats = self.memory.get_stats()

        summary = {
            'statistics': stats,
            'universal_rules': [],
            'conditionals': [],
            'ground_facts': []
        }

        # Get samples of each type
        universals = self.memory.query(type=LogicalType.UNIVERSAL)
        summary['universal_rules'] = [s.raw_text for s in universals[:5]]

        conditionals = self.memory.query(type=LogicalType.CONDITIONAL)
        summary['conditionals'] = [s.raw_text for s in conditionals[:5]]

        grounds = self.memory.query(type=LogicalType.GROUND)
        summary['ground_facts'] = [s.raw_text for s in grounds[:10]]

        return summary

    def clear_memory(self):
        """Clear all stored knowledge"""
        self.memory.clear()
        self.history.clear()

    def reset_conversation(self):
        """Reset conversation history but keep memory"""
        self.history.clear()

    def verify_knowledge_base(self) -> Dict[str, Any]:
        """Verify internal consistency of knowledge base

        Returns:
            Dictionary with verification results
        """
        is_consistent, inconsistencies = self.checker.verify_knowledge_base()

        return {
            'consistent': is_consistent,
            'inconsistencies': inconsistencies,
            'total_statements': self.memory.get_stats()['total']
        }

    def switch_provider(
        self,
        provider_name: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> None:
        """Switch to a different LLM provider

        Args:
            provider_name: New provider name
            api_key: API key (optional)
            model: Model name (optional)
            **kwargs: Additional configuration

        Raises:
            ProviderError: If provider cannot be created
        """
        self.provider = self._create_provider(provider_name, api_key, model, **kwargs)
        self.provider_name = provider_name

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current provider

        Returns:
            Dictionary with provider information
        """
        return self.provider.get_model_info()
