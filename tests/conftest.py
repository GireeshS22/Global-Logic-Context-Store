import pytest
import uuid
import tempfile
import shutil
from pathlib import Path

from glcs.core.memory_manager import MemoryManager
from glcs.core.semantic_encoder import SemanticEncoder
from glcs.advanced_wrapper import AdvancedGLCS
from glcs.core.models import (
    LogicalForm, Entity, Relation, LogicalType, Polarity
)

@pytest.fixture
def memory_manager():
    """Provide an in-memory MemoryManager for each test."""
    # Use unique collection name to ensure test isolation
    collection_name = f"test_{uuid.uuid4().hex[:8]}"
    return MemoryManager(collection_name=collection_name, in_memory=True)

@pytest.fixture
def encoder():
    """Provide a SemanticEncoder for adding embeddings."""
    SemanticEncoder.clear_model_cache()
    return SemanticEncoder()

@pytest.fixture
def advanced_glcs():
    """Provide a full AdvancedGLCS system for each test."""
    collection_name = f"test_adv_{uuid.uuid4().hex[:8]}"
    return AdvancedGLCS(collection_name=collection_name, in_memory=True)

@pytest.fixture
def sample_logical_form():
    """Create a sample LogicalForm without embedding."""
    return LogicalForm(
        context_id="test_session",
        logical_type=LogicalType.UNIVERSAL_RULE,
        subject=Entity(name="humans"),
        predicate=Relation(verb="are"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="All humans are mortal"
    )

@pytest.fixture
def temp_dir():
    """Create a temporary directory for persistent storage tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # Cleanup after test
    shutil.rmtree(temp_path, ignore_errors=True)
