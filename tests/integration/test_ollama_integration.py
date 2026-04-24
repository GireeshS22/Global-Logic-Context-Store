"""
Genuine end-to-end integration tests using a local Ollama instance.
Does NOT mock LLM calls.
"""

import pytest
import requests
from glcs.advanced_wrapper import AdvancedGLCS

def is_ollama_running():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

# Skip all tests in this module if Ollama is not available
pytestmark = pytest.mark.skipif(not is_ollama_running(), reason="Ollama not running on localhost:11434")

class TestOllamaIntegration:
    """End-to-end tests with real LLM parsing."""

    def test_full_pipeline_no_mocks(self, advanced_glcs):
        """Test the complete path from text to memory with a real LLM."""
        # Use a very simple statement
        text = "Socrates is a philosopher"
        context_id = "integ-test-1"
        
        report = advanced_glcs.process_statement(text, context_id)
        
        # Verify success
        assert report.is_consistent is True
        
        # Verify storage
        forms = advanced_glcs.memory.get_forms_by_context(context_id)
        assert len(forms) == 1
        
        # Be flexible with roles as LLM might swap them, but both must be present
        all_text = (forms[0].subject.name + " " + (forms[0].object.name if forms[0].object else "")).lower()
        assert "socrates" in all_text
        assert "philosopher" in all_text

    def test_real_contradiction_detection(self, advanced_glcs):
        """Test that real LLM output triggers contradiction logic."""
        context_id = "integ-test-2"
        
        # Turn 1: Add a simple fact
        advanced_glcs.process_statement("Socrates is a man", context_id)
        
        # Turn 2: Add a direct negation
        report = advanced_glcs.process_statement("Socrates is NOT a man", context_id)
        
        # Should detect contradiction
        assert report.is_consistent is False
        assert len(report.violations) > 0

    def test_real_batch_processing(self, advanced_glcs):
        """Test batch processing with real LLM calls."""
        statements = [
            "Gravity is a force",
            "Water is liquid",
            "Fire is hot"
        ]
        context_id = "integ-test-3"
        
        result = advanced_glcs.process_batch(statements, context_id)
        
        assert result.success_count == 3
        assert result.all_successful is True
        
        # Verify memory
        forms = advanced_glcs.memory.get_forms_by_context(context_id)
        assert len(forms) == 3
