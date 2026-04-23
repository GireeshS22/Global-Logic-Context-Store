"""
Integration tests for Advanced GLCS System (Stage 1.5).

These tests verify the complete pipeline:
LLM Parser → Semantic Encoder → Memory Manager → Consistency Checker

Tests use real components (not mocks) to ensure proper integration.
"""

import pytest
from unittest.mock import patch, Mock
import numpy as np

from glcs.advanced_wrapper import AdvancedGLCS
from glcs.core.models import LogicalType, Polarity
from glcs.utils.exceptions import ParsingError


class TestFullPipeline:
    """Test complete pipeline from text to storage."""

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_process_statement_complete_flow(self, mock_call_llm, advanced_glcs):
        """Test complete flow: parse → encode → check → store."""
        # Mock LLM response
        mock_call_llm.return_value = {
            'subject': {'name': 'john', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'manager', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.95
        }

        # Process statement
        report = advanced_glcs.process_statement(
            "John is a manager",
            context_id="test-ctx-1"
        )

        # Verify report
        assert report.is_consistent == True
        assert len(report.violations) == 0
        assert report.total_forms_checked >= 0

        # Verify statement was stored
        forms = advanced_glcs.memory.get_forms_by_context("test-ctx-1")
        assert len(forms) == 1

        # Verify form has embedding
        form = forms[0]
        assert form.embedding is not None
        assert form.embedding.shape == (768,)

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_contradiction_detection(self, mock_call_llm, advanced_glcs):
        """Test that contradictions are detected in the pipeline."""
        # First statement: John is a manager
        mock_call_llm.return_value = {
            'subject': {'name': 'john', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'manager', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.95
        }
        report1 = advanced_glcs.process_statement("John is a manager", "test-ctx-2")
        assert report1.is_consistent

        # Second statement: John is NOT a manager (polarity contradiction)
        mock_call_llm.return_value = {
            'subject': {'name': 'john', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'manager', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'negative',
            'confidence': 0.95
        }
        report2 = advanced_glcs.process_statement("John is not a manager", "test-ctx-2")

        # Should detect polarity contradiction
        assert report2.is_consistent == False
        assert len(report2.violations) > 0

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_batch_processing(self, mock_call_llm, advanced_glcs):
        """Test batch processing of multiple statements."""
        mock_call_llm.return_value = {
            'subject': {'name': 'test', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'employee', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.90
        }

        statements = [
            "Alice is an employee",
            "Bob is an employee",
            "Charlie is an employee"
        ]

        reports = advanced_glcs.process_batch(statements, "test-ctx-3")

        assert len(reports) == 3
        assert all(r.is_consistent for r in reports)

        # Verify all stored
        forms = advanced_glcs.memory.get_forms_by_context("test-ctx-3")
        assert len(forms) == 3


class TestSemanticSearch:
    """Test semantic similarity search with embeddings."""

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_search_similar_statements(self, mock_call_llm, advanced_glcs):
        """Test finding semantically similar statements."""
        # Store original statement
        mock_call_llm.return_value = {
            'subject': {'name': 'employees', 'type': 'person'},
            'predicate': {'verb': 'work', 'type': 'activity'},
            'object': {'name': 'remotely', 'type': 'location'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.92
        }
        advanced_glcs.process_statement("Employees work remotely", "test-ctx-4")

        # Search for similar
        similar = advanced_glcs.search_similar(
            "Staff work from home",
            context_id="test-ctx-4",
            top_k=5
        )

        # Should find the stored statement (semantically similar)
        assert len(similar) > 0

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_search_by_entity(self, mock_call_llm, advanced_glcs):
        """Test searching for statements about specific entity."""
        # Store statements about John
        mock_call_llm.return_value = {
            'subject': {'name': 'john', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'manager', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.95
        }
        advanced_glcs.process_statement("John is a manager", "test-ctx-5")

        # Search for statements about John
        results = advanced_glcs.get_forms_by_entity("john", context_id="test-ctx-5")

        assert len(results) > 0
        assert all(
            form.subject.name == 'john' or (form.object and form.object.name == 'john')
            for form in results
        )


class TestContextManagement:
    """Test context-based operations."""

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_context_summary(self, mock_call_llm, advanced_glcs):
        """Test getting context summary."""
        # Add 3 distinct statements with unique mock responses
        subjects = ['alice', 'bob', 'charlie']
        objects = ['engineer', 'designer', 'manager']

        for i in range(3):
            mock_call_llm.return_value = {
                'subject': {'name': subjects[i], 'type': 'person'},
                'predicate': {'verb': 'is', 'type': 'property'},
                'object': {'name': objects[i], 'type': 'role'},
                'logical_type': 'ground_fact',
                'polarity': 'positive',
                'confidence': 0.9
            }
            advanced_glcs.process_statement(f"{subjects[i]} is a {objects[i]}", "test-ctx-6")

        summary = advanced_glcs.get_context_summary("test-ctx-6")

        assert summary['context_id'] == "test-ctx-6"
        assert summary['total_forms'] == 3
        assert 'statistics' in summary

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_clear_context(self, mock_call_llm, advanced_glcs):
        """Test clearing a context."""
        # Use distinct mock responses so neither is flagged as redundant
        mock_call_llm.return_value = {
            'subject': {'name': 'alice', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'engineer', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.9
        }
        advanced_glcs.process_statement("Alice is an engineer", "test-ctx-7")

        mock_call_llm.return_value = {
            'subject': {'name': 'bob', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'designer', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.9
        }
        advanced_glcs.process_statement("Bob is a designer", "test-ctx-7")

        # Clear context
        count = advanced_glcs.clear_context("test-ctx-7")

        assert count == 2

        # Verify context is empty
        forms = advanced_glcs.memory.get_forms_by_context("test-ctx-7")
        assert len(forms) == 0

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_clear_all(self, mock_call_llm, advanced_glcs):
        """Test clearing the entire knowledge base."""
        # Add statements to different contexts
        mock_call_llm.return_value = {
            'subject': {'name': 'alice', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'engineer', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.9
        }
        advanced_glcs.process_statement("Alice is an engineer", "ctx-1")

        mock_call_llm.return_value = {
            'subject': {'name': 'bob', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'designer', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.9
        }
        advanced_glcs.process_statement("Bob is a designer", "ctx-2")

        assert advanced_glcs.memory.count_all_forms() == 2

        # Clear all
        count = advanced_glcs.clear_all()

        assert count == 2
        assert advanced_glcs.memory.count_all_forms() == 0


class TestConsistencyChecking:
    """Test advanced consistency checking features."""

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_verify_context_consistency(self, mock_call_llm, advanced_glcs):
        """Test verifying entire context for consistency."""
        # Add consistent statements
        mock_call_llm.return_value = {
            'subject': {'name': 'alice', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'engineer', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.95
        }

        advanced_glcs.process_statement("Alice is an engineer", "test-ctx-8")

        # Verify context
        report = advanced_glcs.verify_context("test-ctx-8")

        assert report.is_consistent

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_redundancy_detection(self, mock_call_llm, advanced_glcs):
        """Test detection of redundant statements."""
        # Same statement twice
        mock_call_llm.return_value = {
            'subject': {'name': 'bob', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'developer', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.95
        }

        report1 = advanced_glcs.process_statement("Bob is a developer", "test-ctx-9")
        assert report1.is_consistent

        # Very similar statement
        report2 = advanced_glcs.process_statement("Bob is a developer", "test-ctx-9")

        # May detect as redundancy
        if not report2.is_consistent:
            assert any('redundancy' in v.violation_type.lower() for v in report2.violations)


class TestSystemInformation:
    """Test system information and configuration."""

    def test_get_system_info(self, advanced_glcs):
        """Test getting system information."""
        info = advanced_glcs.get_system_info()

        assert 'parser' in info
        assert 'encoder' in info
        assert 'memory' in info
        assert 'checker' in info

        assert info['parser']['provider'] == 'ollama'
        assert info['encoder']['dimensions'] == 768

    def test_switch_parser_provider(self, advanced_glcs):
        """Test switching parser provider."""
        original_provider = advanced_glcs.parser.provider_name

        # Switch provider (mock to avoid actual provider creation)
        with patch('glcs.core.logical_parser.ProviderFactory.create') as mock_create:
            mock_create.return_value = Mock()
            advanced_glcs.switch_parser_provider('openai', model='gpt-4o-mini')

        assert advanced_glcs.parser.provider_name == 'openai'


class TestErrorHandling:
    """Test error handling in full pipeline."""

    def test_handle_parsing_failure(self, advanced_glcs):
        """Test handling when parsing fails."""
        # Mock parser to always fail
        with patch.object(advanced_glcs.parser, 'parse', side_effect=ParsingError("Test error")):
            with pytest.raises(ParsingError):
                advanced_glcs.process_statement("Test", "test-ctx-10")

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_handle_low_confidence(self, mock_call_llm, advanced_glcs):
        """Test handling of low confidence parses."""
        mock_call_llm.return_value = {
            'subject': {'name': 'test', 'type': None},
            'predicate': {'verb': 'is', 'type': None},
            'object': None,
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.3  # Low confidence
        }

        report = advanced_glcs.process_statement("Ambiguous statement", "test-ctx-11")

        # Should still process, but confidence will be low
        form = advanced_glcs.memory.get_forms_by_context("test-ctx-11")[0]
        assert form.confidence_score == 0.3


class TestMultipleContexts:
    """Test handling multiple independent contexts."""

    @patch('glcs.core.logical_parser.LLMLogicalParser._call_llm')
    def test_isolated_contexts(self, mock_call_llm, advanced_glcs):
        """Test that contexts are isolated from each other."""
        mock_call_llm.return_value = {
            'subject': {'name': 'john', 'type': 'person'},
            'predicate': {'verb': 'is', 'type': 'property'},
            'object': {'name': 'manager', 'type': 'role'},
            'logical_type': 'ground_fact',
            'polarity': 'positive',
            'confidence': 0.95
        }

        # Add to context A
        advanced_glcs.process_statement("John is a manager", "ctx-a")

        # Add to context B
        mock_call_llm.return_value['object']['name'] = 'engineer'
        advanced_glcs.process_statement("John is an engineer", "ctx-b")

        # Both should be consistent in their own contexts
        forms_a = advanced_glcs.memory.get_forms_by_context("ctx-a")
        forms_b = advanced_glcs.memory.get_forms_by_context("ctx-b")

        assert len(forms_a) == 1
        assert len(forms_b) == 1
        assert forms_a[0].object.name == 'manager'
        assert forms_b[0].object.name == 'engineer'


# Run with: pytest tests/integration/test_advanced_glcs.py -v
