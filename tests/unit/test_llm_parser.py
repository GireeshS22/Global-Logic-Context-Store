"""
Unit tests for LLM-based Logical Parser (Stage 1.5).

Tests cover:
- Basic parsing functionality
- Entity and relation extraction
- Logical type classification
- Polarity detection
- Confidence scoring
- Error handling and retries
- Caching mechanism
- Batch processing
- Provider switching
- Integration with LogicalForm model
"""

import pytest
import json
import copy
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from glcs.core.logical_parser import LLMLogicalParser
from glcs.core.models import LogicalForm, LogicalType, Polarity
from glcs.utils.exceptions import ParsingError, ValidationError
from glcs.providers import ProviderError


class TestLLMLogicalParserInitialization:
    """Test parser initialization and configuration."""

    def test_init_with_default_provider(self):
        """Test initialization with default Ollama provider."""
        parser = LLMLogicalParser()
        assert parser.provider_name == 'ollama'
        assert parser.cache_enabled == True
        assert parser.max_retries == 3

    def test_init_with_specific_provider(self):
        """Test initialization with specific provider."""
        with patch('glcs.core.logical_parser.ProviderFactory.create') as mock_factory:
            mock_factory.return_value = Mock()
            parser = LLMLogicalParser(provider='openai', model='gpt-4o-mini')
            assert parser.provider_name == 'openai'

    def test_init_with_cache_disabled(self):
        """Test initialization with caching disabled."""
        parser = LLMLogicalParser(cache_enabled=False)
        assert parser.cache_enabled == False
        assert parser.cache == {}

    def test_init_with_custom_retries(self):
        """Test initialization with custom retry count."""
        parser = LLMLogicalParser(max_retries=5)
        assert parser.max_retries == 5

    def test_get_default_model(self):
        """Test default model selection for each provider."""
        parser = LLMLogicalParser()
        assert parser._get_default_model('ollama') == 'qwen2.5:0.5b'
        assert parser._get_default_model('openai') == 'gpt-4o-mini'
        assert parser._get_default_model('anthropic') == 'claude-3-5-sonnet-20241022'


class TestBasicParsing:
    """Test basic parsing functionality."""

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_parse_simple_ground_fact(self, mock_call_llm):
        """Test parsing a simple ground fact."""
        mock_call_llm.return_value = {
            'subject': {'name': 'john', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'manager', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.95
        }

        parser = LLMLogicalParser()
        form = parser.parse("John is a manager", "ctx-123")

        assert isinstance(form, LogicalForm)
        assert form.subject.name == 'john'
        assert form.predicate.verb == 'is'
        assert form.object.name == 'manager'
        assert form.logical_type == LogicalType.GROUND_FACT
        assert form.polarity == Polarity.POSITIVE
        assert form.confidence_score == 0.95
        assert form.source_text == "John is a manager"
        assert form.context_id == "ctx-123"

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_parse_universal_rule(self, mock_call_llm):
        """Test parsing a universal rule."""
        mock_call_llm.return_value = {
            'subject': {'name': 'employees', 'type': 'person'},
            'predicate': {'verb': 'must_complete', 'type': 'requirement'},
            'object': {'name': 'training', 'type': 'activity'},
            'logical_type': 'universal_rule',
            'polarity': 'positive',
            'confidence': 0.92
        }

        parser = LLMLogicalParser()
        form = parser.parse("All employees must complete training", "ctx-123")

        assert form.logical_type == LogicalType.UNIVERSAL_RULE
        assert form.subject.name == 'employees'

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_parse_conditional_logic(self, mock_call_llm):
        """Test parsing conditional statement."""
        mock_call_llm.return_value = {
            'subject': {'name': 'server', 'type': 'system'},
            'predicate': {'verb': 'crashes_then_restarts', 'type': 'causation'},
            'object': {'name': 'restart', 'type': 'action'},
            'logical_type': 'conditional_logic',
            'polarity': 'positive',
            'confidence': 0.88
        }

        parser = LLMLogicalParser()
        form = parser.parse("If server crashes, it restarts", "ctx-123")

        assert form.logical_type == LogicalType.CONDITIONAL_LOGIC

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_parse_negative_statement(self, mock_call_llm):
        """Test parsing negative polarity statement."""
        mock_call_llm.return_value = {
            'subject': {'name': 'alice', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'engineer', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'negative',
            'confidence': 0.96
        }

        parser = LLMLogicalParser()
        form = parser.parse("Alice is not an engineer", "ctx-123")

        assert form.polarity == Polarity.NEGATIVE

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_parse_unary_predicate(self, mock_call_llm):
        """Test parsing statement with no object (unary predicate)."""
        mock_call_llm.return_value = {
            'subject': {'name': 'socrates', 'type': 'person'},
            'predicate': {'verb': 'exists', 'type': 'existence'},
            'object': None,
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.99
        }

        parser = LLMLogicalParser()
        form = parser.parse("Socrates exists", "ctx-123")

        assert form.object is None


class TestComplexSentences:
    """Test parsing of complex sentences that regex can't handle."""

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_parse_with_modifiers(self, mock_call_llm):
        """Test parsing sentence with modifying clauses."""
        mock_call_llm.return_value = {
            'subject': {'name': 'john', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'manager', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.90
        }

        parser = LLMLogicalParser()
        form = parser.parse("John, who joined last month, is a senior manager", "ctx-123")

        assert form.subject.name == 'john'
        assert form.object.name == 'manager'

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_parse_with_prepositional_phrases(self, mock_call_llm):
        """Test parsing with prepositional phrases."""
        mock_call_llm.return_value = {
            'subject': {'name': 'meeting', 'type': 'event'},
            'predicate': {'verb': 'scheduled_for', 'type': 'temporal'},
            'object': {'name': 'monday', 'type': 'time'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.87
        }

        parser = LLMLogicalParser()
        form = parser.parse("The meeting in the conference room is scheduled for Monday", "ctx-123")

        assert isinstance(form, LogicalForm)


class TestEntityAndRelationExtraction:
    """Test entity and relation extraction accuracy."""

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_entity_normalization(self, mock_call_llm):
        """Test that entity names are normalized to lowercase."""
        mock_call_llm.return_value = {
            'subject': {'name': 'JOHN', 'type': 'person'},
            'predicate': {'verb': 'IS', 'type': 'property'},
            'object': {'name': 'MANAGER', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.95
        }

        parser = LLMLogicalParser()
        form = parser.parse("JOHN IS A MANAGER", "ctx-123")

        # Parser normalizes to lowercase in _create_logical_form
        assert form.subject.name == 'john'
        assert form.object.name == 'manager'

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_entity_type_extraction(self, mock_call_llm):
        """Test extraction of entity types."""
        mock_call_llm.return_value = {
            'subject': {'name': 'server', 'type': 'system'},
            'predicate': {'verb': 'is', 'type': 'state'},
            'object': {'name': 'online', 'type': 'status'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.93
        }

        parser = LLMLogicalParser()
        form = parser.parse("The server is online", "ctx-123")

        assert form.subject.entity_type == 'system'
        assert form.object.entity_type == 'status'

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_relation_type_extraction(self, mock_call_llm):
        """Test extraction of relation types."""
        mock_call_llm.return_value = {
            'subject': {'name': 'alice', 'type': 'person'},
            'predicate': {'verb': 'works_in', 'type': 'location'},
            'object': {'name': 'engineering', 'type': 'department'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.94
        }

        parser = LLMLogicalParser()
        form = parser.parse("Alice works in engineering", "ctx-123")

        assert form.predicate.relation_type == 'location'


class TestValidation:
    """Test validation of LLM outputs."""

    def test_validate_missing_required_field(self):
        """Test validation fails if required field is missing."""
        parser = LLMLogicalParser()

        with pytest.raises(ValidationError, match="Missing required field"):
            parser._validate_extraction({
                'subject': {'name': 'test'},
                # Missing 'predicate'
                'logical_type': 'ground_fact',
                'polarity': 'positive',
                'confidence': 0.9
            })

    def test_validate_invalid_logical_type(self):
        """Test validation fails on invalid logical type."""
        parser = LLMLogicalParser()

        with pytest.raises(ValidationError, match="Invalid logical_type"):
            parser._validate_extraction({
                'subject': {'name': 'test'},
                'predicate': {'verb': 'is'},
                'logical_type': 'invalid_type',
                'polarity': 'positive',
                'confidence': 0.9
            })

    def test_validate_invalid_polarity(self):
        """Test validation fails on invalid polarity."""
        parser = LLMLogicalParser()

        with pytest.raises(ValidationError, match="Invalid polarity"):
            parser._validate_extraction({
                'subject': {'name': 'test'},
                'predicate': {'verb': 'is'},
                'logical_type': 'ground_fact',
                'polarity': 'invalid',
                'confidence': 0.9
            })

    def test_validate_invalid_confidence(self):
        """Test validation fails on out-of-range confidence."""
        parser = LLMLogicalParser()

        with pytest.raises(ValidationError, match="Invalid confidence"):
            parser._validate_extraction({
                'subject': {'name': 'test'},
                'predicate': {'verb': 'is'},
                'logical_type': 'ground_fact',
                'polarity': 'positive',
                'confidence': 1.5  # Out of range
            })

    def test_validate_invalid_subject_structure(self):
        """Test validation fails if subject structure is invalid."""
        parser = LLMLogicalParser()

        with pytest.raises(ValidationError, match="Invalid subject structure"):
            parser._validate_extraction({
                'subject': "not a dict",
                'predicate': {'verb': 'is'},
                'logical_type': 'ground_fact',
                'polarity': 'positive',
                'confidence': 0.9
            })

    def test_validate_extraction_is_pure(self):
        """Test that _validate_extraction does not mutate input dict (#71)."""
        parser = LLMLogicalParser()

        # Minimal input that needs defaults
        input_data = {
            'subject': {'name': 'test'},
            'predicate': {'verb': 'is'}
        }

        input_copy = copy.deepcopy(input_data)

        validated = parser._validate_extraction(input_data)

        # Original should be untouched
        assert input_data == input_copy

        # New dict should have defaults
        assert 'logical_type' in validated
        assert 'polarity' in validated
        assert 'confidence' in validated
        assert validated['confidence'] == 0.7



class TestErrorHandling:
    """Test error handling and retry logic."""

    def test_parse_empty_text(self):
        """Test parsing empty text raises ValidationError."""
        parser = LLMLogicalParser()

        with pytest.raises(ValidationError, match="Cannot parse empty text"):
            parser.parse("", "ctx-123")

    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only text raises ValidationError."""
        parser = LLMLogicalParser()

        with pytest.raises(ValidationError, match="Cannot parse empty text"):
            parser.parse("   \n  ", "ctx-123")

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_retry_on_failure(self, mock_call_llm):
        """Test retry logic on temporary failures."""
        # First two calls fail, third succeeds
        mock_call_llm.side_effect = [
            ParsingError("Temporary error"),
            ParsingError("Another error"),
            {
                'subject': {'name': 'test', 'type': None},
                'predicate': {'verb': 'is', 'type': None},
                'object': None,
                'logical_type': 'ground_fact',
                'polarity': 'positive',
                'confidence': 0.9
            }
        ]

        parser = LLMLogicalParser(max_retries=3)
        form = parser.parse("Test statement", "ctx-123")

        assert form.subject.name == 'test'
        assert mock_call_llm.call_count == 3

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_max_retries_exceeded(self, mock_call_llm):
        """Test parsing fails after max retries."""
        mock_call_llm.side_effect = ParsingError("Persistent error")

        parser = LLMLogicalParser(max_retries=2)

        with pytest.raises(ParsingError, match="Failed to parse after 2 attempts"):
            parser.parse("Test statement", "ctx-123")

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_invalid_json_response(self, mock_call_llm):
        """Test handling of invalid JSON from LLM."""
        parser = LLMLogicalParser()

        # Mock _call_llm to raise ParsingError
        mock_call_llm.side_effect = ParsingError("Invalid JSON")

        with pytest.raises(ParsingError):
            parser.parse("Test", "ctx-123")


class TestCaching:
    """Test caching mechanism."""

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_cache_hit(self, mock_call_llm):
        """Test that cached results are returned without calling LLM."""
        mock_call_llm.return_value = {
            'subject': {'name': 'test', 'type': None},
            'predicate': {'verb': 'is', 'type': None},
            'object': None,
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.9
        }

        parser = LLMLogicalParser(cache_enabled=True)

        # First call - cache miss
        form1 = parser.parse("Test statement", "ctx-123")
        assert mock_call_llm.call_count == 1

        # Second call with same text - cache hit
        form2 = parser.parse("Test statement", "ctx-456")
        assert mock_call_llm.call_count == 1  # Not called again

        # Forms should be identical except for context_id
        assert form1.subject.name == form2.subject.name
        assert form2.context_id == "ctx-456"  # Updated context

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_cache_disabled(self, mock_call_llm):
        """Test that caching can be disabled."""
        mock_call_llm.return_value = {
            'subject': {'name': 'test', 'type': None},
            'predicate': {'verb': 'is', 'type': None},
            'object': None,
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.9
        }

        parser = LLMLogicalParser(cache_enabled=False)

        parser.parse("Test statement", "ctx-123")
        parser.parse("Test statement", "ctx-123")

        # Should call LLM both times
        assert mock_call_llm.call_count == 2

    def test_clear_cache(self):
        """Test clearing the cache."""
        parser = LLMLogicalParser()
        parser.cache = {'key1': 'value1', 'key2': 'value2'}

        count = parser.clear_cache()

        assert count == 2
        assert len(parser.cache) == 0

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        parser = LLMLogicalParser()
        parser.cache = {'key1': Mock(), 'key2': Mock()}

        stats = parser.get_cache_stats()

        assert stats['enabled'] == True
        assert stats['size'] == 2
        assert stats['provider'] == 'ollama'


class TestBatchProcessing:
    """Test batch processing functionality."""

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_parse_batch_success(self, mock_call_llm):
        """Test successful batch parsing."""
        mock_call_llm.return_value = {
            'subject': {'name': 'test', 'type': None},
            'predicate': {'verb': 'is', 'type': None},
            'object': None,
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.9
        }

        parser = LLMLogicalParser()
        texts = ["Statement 1", "Statement 2", "Statement 3"]
        result = parser.parse_batch(texts, "ctx-123")

        assert result.success_count == 3
        assert result.total_count == 3
        assert result.all_successful is True
        for form in result.successes:
            assert form.context_id == "ctx-123"

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_parse_batch_partial_failure(self, mock_call_llm):
        """Test batch parsing with some failures."""
        # First call succeeds, second fails, third succeeds
        mock_call_llm.side_effect = [
            {'subject': {'name': 'test1'}, 'predicate': {'verb': 'is'},
             'logical_type': 'ground_fact', 'polarity': 'positive', 'confidence': 0.9},
            ParsingError("Failed"),
            {'subject': {'name': 'test3'}, 'predicate': {'verb': 'is'},
             'logical_type': 'ground_fact', 'polarity': 'positive', 'confidence': 0.9},
        ]

        parser = LLMLogicalParser(max_retries=1)
        texts = ["Statement 1", "Statement 2", "Statement 3"]
        result = parser.parse_batch(texts, "ctx-123")

        # Should get 2 out of 3
        assert result.success_count == 2
        assert result.total_count == 3
        assert result.error_count == 1
        assert result.all_successful is False
        assert result.errors[0]['index'] == 1


class TestProviderSwitching:
    """Test switching between LLM providers."""

    @patch('glcs.core.logical_parser.ProviderFactory.create')
    def test_switch_provider(self, mock_factory):
        """Test switching to different provider."""
        mock_provider1 = Mock()
        mock_provider2 = Mock()
        mock_factory.side_effect = [mock_provider1, mock_provider2]

        parser = LLMLogicalParser(provider='ollama')
        assert parser.provider_name == 'ollama'

        parser.switch_provider('openai', model='gpt-4o')
        assert parser.provider_name == 'openai'

    @patch('glcs.core.logical_parser.ProviderFactory.create')
    def test_switch_provider_clears_cache(self, mock_factory):
        """Test that switching providers clears the cache."""
        mock_factory.return_value = Mock()

        parser = LLMLogicalParser()
        parser.cache = {'key': Mock()}

        parser.switch_provider('openai')

        assert len(parser.cache) == 0

    @patch('glcs.core.logical_parser.ProviderFactory.create')
    def test_switch_provider_atomic_failure(self, mock_factory):
        """Test that failure to create new provider leaves parser unchanged (#70)."""
        mock_provider = Mock()
        # First call (init) succeeds, second call (switch) fails
        mock_factory.side_effect = [mock_provider, Exception("Failed to create provider")]

        parser = LLMLogicalParser(provider='ollama', model='old-model')
        assert parser.provider_name == 'ollama'
        assert parser._model == 'old-model'

        # Switch should fail
        with pytest.raises(Exception, match="Failed to create provider"):
            parser.switch_provider('openai', model='new-model')

        # State should still be original
        assert parser.provider_name == 'ollama'
        assert parser._model == 'old-model'
        assert parser.provider == mock_provider


class TestIntegrationWithLogicalForm:
    """Test integration with LogicalForm model."""

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_logical_form_validation(self, mock_call_llm):
        """Test that created LogicalForm passes validation."""
        mock_call_llm.return_value = {
            'subject': {'name': 'test', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'manager', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.95
        }

        parser = LLMLogicalParser()
        form = parser.parse("Test statement", "ctx-123")

        # LogicalForm model validation should pass
        assert isinstance(form, LogicalForm)
        assert form.form_id is not None
        assert isinstance(form.timestamp, datetime)

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_confidence_score_range(self, mock_call_llm):
        """Test that confidence scores are within valid range."""
        mock_call_llm.return_value = {
            'subject': {'name': 'test', 'type': None},
            'predicate': {'verb': 'is', 'type': None},
            'object': None,
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.95
        }

        parser = LLMLogicalParser()
        form = parser.parse("Test", "ctx-123")

        assert 0.0 <= form.confidence_score <= 1.0


# Run tests with: pytest tests/unit/test_llm_parser.py -v
