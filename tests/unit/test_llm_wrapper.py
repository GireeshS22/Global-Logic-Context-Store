"""
Unit tests for GLCSWrapper (glcs/llm_wrapper.py).

Tests focus on the generate() method's context-augmentation behaviour and
the interaction between history and LLM messages.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def wrapper():
    """GLCSWrapper with all external dependencies mocked."""
    with patch("glcs.llm_wrapper.load_dotenv"):
        from glcs.providers.base import LLMProvider
        from glcs.llm_wrapper import GLCSWrapper

        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.generate.return_value = "Test response"
        mock_provider.get_provider_name.return_value = "mock"

        # Pass the provider instance directly — bypasses _create_provider entirely
        w = GLCSWrapper(provider=mock_provider)
        return w


class TestContextAugmentation:
    """#43 — augmented_prompt must be sent to the LLM, not dropped."""

    def test_context_reaches_llm_when_memory_has_facts(self, wrapper):
        """When _build_context returns content, LLM messages must include it."""
        wrapper._build_context = MagicMock(return_value="Known facts:\n- All humans are mortal")

        with patch.object(wrapper, "check_and_store", return_value=(True, [])):
            wrapper.generate("Is Socrates mortal?", check_consistency=False)

        call_messages = wrapper.provider.generate.call_args[0][0]
        combined = " ".join(m["content"] for m in call_messages)
        assert "Known facts" in combined, "Context must appear in messages sent to LLM"
        assert "Is Socrates mortal?" in combined

    def test_history_stores_original_prompt_not_augmented(self, wrapper):
        """History must contain the original prompt, not the context-augmented version."""
        wrapper._build_context = MagicMock(return_value="Known facts:\n- All humans are mortal")

        with patch.object(wrapper, "check_and_store", return_value=(True, [])):
            wrapper.generate("Is Socrates mortal?", check_consistency=False)

        user_messages_in_history = [
            m["content"] for m in wrapper.history if m["role"] == "user"
        ]
        assert any("Is Socrates mortal?" in c for c in user_messages_in_history)
        assert not any("Known facts" in c for c in user_messages_in_history), \
            "History should not be polluted with augmented context"

    def test_no_augmentation_when_memory_empty(self, wrapper):
        """When _build_context returns empty string, messages use plain prompt."""
        wrapper._build_context = MagicMock(return_value="")

        with patch.object(wrapper, "check_and_store", return_value=(True, [])):
            wrapper.generate("Hello", check_consistency=False)

        call_messages = wrapper.provider.generate.call_args[0][0]
        user_msg = next(m for m in reversed(call_messages) if m["role"] == "user")
        assert user_msg["content"] == "Hello"


class TestValidateConfig:
    """#44 — validate_config dead return value."""

    def test_validate_config_returns_none(self):
        """validate_config should return None — it raises on failure, never False."""
        from glcs.utils.config_manager import validate_config
        config = {
            "memory": {"vector_dimension": 768, "similarity_threshold": 0.8},
            "encoder": {"model_name": "all-mpnet-base-v2", "batch_size": 32},
            "consistency": {"contradiction_threshold": 0.85},
            "parser": {},
            "logging": {},
        }
        result = validate_config(config)
        assert result is None, "validate_config should return None, not True"

class TestHistorySlidingWindow:
    """#79 — History must not grow without limit."""

    def test_history_sliding_window_enforcement(self, wrapper):
        """History should only keep the last max_history items."""
        wrapper.max_history = 5
        
        # Mock consistency check to avoid overhead
        with patch.object(wrapper, "check_and_store", return_value=(True, [])):
            # Generate 10 rounds of conversation (20 messages total: 10 user, 10 assistant)
            for i in range(10):
                wrapper.generate(f"Prompt {i}", check_consistency=False)
        
        # Each generate adds 2 messages (user prompt + assistant response)
        # With max_history=5, we should only have the last 5 messages.
        assert len(wrapper.history) == 5
        assert wrapper.history[-1]["content"] == "Test response"
        assert wrapper.history[-2]["content"] == "Prompt 9"
