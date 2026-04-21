"""
Unit tests for Memory Manager (Stage 1.2).

Tests the MemoryManager class which provides persistent storage for LogicalForm
objects using ChromaDB as the vector database backend.

Test Coverage:
    - Initialization (in-memory and persistent)
    - CRUD operations
    - Query operations (context, similarity, entity, relation)
    - Context management
    - Error handling
    - Integration with SemanticEncoder
"""

import pytest
import numpy as np
from uuid import UUID
from pathlib import Path

from glcs.core.memory_manager import MemoryManager
from glcs.core.semantic_encoder import SemanticEncoder
from glcs.core.models import (
    LogicalForm,
    Entity,
    Relation,
    LogicalType,
    Polarity
)
from glcs.utils.exceptions import GLCSMemoryError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_logical_forms():
    """Create multiple sample LogicalForms without embeddings."""
    return [
        LogicalForm(
            context_id="session_1",
            logical_type=LogicalType.UNIVERSAL_RULE,
            subject=Entity(name="humans"),
            predicate=Relation(verb="are"),
            object=Entity(name="mortal"),
            polarity=Polarity.POSITIVE,
            source_text="All humans are mortal"
        ),
        LogicalForm(
            context_id="session_1",
            logical_type=LogicalType.GROUND_FACT,
            subject=Entity(name="socrates"),
            predicate=Relation(verb="is"),
            object=Entity(name="human"),
            polarity=Polarity.POSITIVE,
            source_text="Socrates is human"
        ),
        LogicalForm(
            context_id="session_2",
            logical_type=LogicalType.GROUND_FACT,
            subject=Entity(name="socrates"),
            predicate=Relation(verb="is"),
            object=Entity(name="mortal"),
            polarity=Polarity.POSITIVE,
            source_text="Socrates is mortal"
        )
    ]


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

def test_memory_manager_in_memory_initialization():
    """Test initialization with in-memory storage."""
    manager = MemoryManager(in_memory=True)
    assert manager.collection_name == "logical_forms"
    assert manager.in_memory is True
    assert manager.collection is not None
    assert manager.count_all_forms() == 0


def test_memory_manager_persistent_initialization(temp_dir):
    """Test initialization with persistent storage."""
    manager = MemoryManager(
        persist_directory=temp_dir,
        in_memory=False
    )
    assert manager.collection_name == "logical_forms"
    assert manager.in_memory is False
    assert manager.collection is not None

    # Verify directory was created
    assert Path(temp_dir).exists()


def test_memory_manager_custom_collection_name():
    """Test initialization with custom collection name."""
    manager = MemoryManager(
        collection_name="test_collection",
        in_memory=True
    )
    assert manager.collection_name == "test_collection"


# ============================================================================
# CRUD OPERATION TESTS
# ============================================================================

def test_store_form(memory_manager, encoder, sample_logical_form):
    """Test storing a LogicalForm."""
    # Add embedding
    encoder.add_embedding_to_form(sample_logical_form)

    # Store form
    form_id = memory_manager.store_form(sample_logical_form)

    assert form_id == sample_logical_form.form_id
    assert memory_manager.count_all_forms() == 1


def test_store_form_without_embedding_raises_error(memory_manager, sample_logical_form):
    """Test that storing form without embedding raises error."""
    with pytest.raises(GLCSMemoryError, match="without embedding"):
        memory_manager.store_form(sample_logical_form)


def test_retrieve_form(memory_manager, encoder, sample_logical_form):
    """Test retrieving a stored LogicalForm."""
    # Store form
    encoder.add_embedding_to_form(sample_logical_form)
    form_id = memory_manager.store_form(sample_logical_form)

    # Retrieve form
    retrieved = memory_manager.retrieve_form(form_id)

    assert retrieved.form_id == sample_logical_form.form_id
    assert retrieved.source_text == sample_logical_form.source_text
    assert retrieved.context_id == sample_logical_form.context_id
    assert retrieved.embedding is not None
    assert retrieved.embedding.shape == (768,)


def test_retrieve_nonexistent_form_raises_error(memory_manager):
    """Test that retrieving non-existent form raises error."""
    from uuid import uuid4
    fake_id = uuid4()

    with pytest.raises(GLCSMemoryError, match="Form not found"):
        memory_manager.retrieve_form(fake_id)


def test_update_form(memory_manager, encoder, sample_logical_form):
    """Test updating an existing LogicalForm."""
    # Store original form
    encoder.add_embedding_to_form(sample_logical_form)
    form_id = memory_manager.store_form(sample_logical_form)

    # Modify form
    sample_logical_form.confidence_score = 0.75
    sample_logical_form.source_text = "Modified: All humans are mortal"
    encoder.add_embedding_to_form(sample_logical_form)  # Re-encode

    # Update
    memory_manager.update_form(form_id, sample_logical_form)

    # Retrieve and verify
    updated = memory_manager.retrieve_form(form_id)
    assert updated.confidence_score == 0.75
    assert updated.source_text == "Modified: All humans are mortal"


def test_update_nonexistent_form_raises_error(memory_manager, encoder, sample_logical_form):
    """Test that updating non-existent form raises error."""
    from uuid import uuid4
    fake_id = uuid4()

    encoder.add_embedding_to_form(sample_logical_form)

    with pytest.raises(GLCSMemoryError, match="Cannot update non-existent"):
        memory_manager.update_form(fake_id, sample_logical_form)


def test_delete_form(memory_manager, encoder, sample_logical_form):
    """Test deleting a LogicalForm."""
    # Store form
    encoder.add_embedding_to_form(sample_logical_form)
    form_id = memory_manager.store_form(sample_logical_form)

    assert memory_manager.count_all_forms() == 1

    # Delete form
    memory_manager.delete_form(form_id)

    assert memory_manager.count_all_forms() == 0

    # Verify it's gone
    with pytest.raises(GLCSMemoryError, match="Form not found"):
        memory_manager.retrieve_form(form_id)


# ============================================================================
# QUERY OPERATION TESTS
# ============================================================================

def test_get_forms_by_context(memory_manager, encoder, sample_logical_forms):
    """Test retrieving forms by context ID."""
    # Store forms (2 in session_1, 1 in session_2)
    for form in sample_logical_forms:
        encoder.add_embedding_to_form(form)
        memory_manager.store_form(form)

    # Get forms from session_1
    session1_forms = memory_manager.get_forms_by_context("session_1")
    assert len(session1_forms) == 2

    # Get forms from session_2
    session2_forms = memory_manager.get_forms_by_context("session_2")
    assert len(session2_forms) == 1


def test_get_forms_by_context_empty(memory_manager):
    """Test getting forms from non-existent context returns empty list."""
    forms = memory_manager.get_forms_by_context("nonexistent")
    assert forms == []


def test_search_similar_forms(memory_manager, encoder, sample_logical_forms):
    """Test semantic similarity search."""
    # Store forms
    for form in sample_logical_forms:
        encoder.add_embedding_to_form(form)
        memory_manager.store_form(form)

    # Search for similar forms to "All humans are mortal"
    query_text = "Every person is mortal"
    query_embedding = encoder.encode(query_text)

    similar = memory_manager.search_similar_forms(query_embedding, top_k=3)

    assert len(similar) <= 3
    assert all(isinstance(form, LogicalForm) for form in similar)
    # Most similar should be the "humans are mortal" form
    assert "humans" in similar[0].source_text.lower() or "mortal" in similar[0].source_text.lower()


def test_search_similar_forms_with_context_filter(memory_manager, encoder, sample_logical_forms):
    """Test similarity search with context filtering."""
    # Store forms
    for form in sample_logical_forms:
        encoder.add_embedding_to_form(form)
        memory_manager.store_form(form)

    # Search only in session_1
    query_embedding = encoder.encode("Socrates is human")
    similar = memory_manager.search_similar_forms(
        query_embedding,
        top_k=5,
        context_id="session_1"
    )

    # Should only return forms from session_1
    assert all(form.context_id == "session_1" for form in similar)
    assert len(similar) == 2  # Only 2 forms in session_1


def test_search_similar_forms_wrong_dimension_raises_error(memory_manager):
    """Test that wrong embedding dimension raises error."""
    wrong_embedding = np.random.rand(512)  # Wrong size

    with pytest.raises(GLCSMemoryError, match="must be 768-dimensional"):
        memory_manager.search_similar_forms(wrong_embedding)


def test_search_by_entity(memory_manager, encoder, sample_logical_forms):
    """Test searching by entity name."""
    # Store forms
    for form in sample_logical_forms:
        encoder.add_embedding_to_form(form)
        memory_manager.store_form(form)

    # Search for "socrates"
    socrates_forms = memory_manager.search_by_entity("socrates")

    assert len(socrates_forms) == 2  # 2 forms mention Socrates
    assert all("socrates" in form.source_text.lower() for form in socrates_forms)


def test_search_by_entity_no_results(memory_manager, encoder, sample_logical_forms):
    """Test searching for non-existent entity."""
    # Store forms
    for form in sample_logical_forms:
        encoder.add_embedding_to_form(form)
        memory_manager.store_form(form)

    # Search for entity that doesn't exist
    results = memory_manager.search_by_entity("plato")
    assert results == []


def test_search_by_relation(memory_manager, encoder, sample_logical_forms):
    """Test searching by relation/predicate."""
    # Store forms
    for form in sample_logical_forms:
        encoder.add_embedding_to_form(form)
        memory_manager.store_form(form)

    # Search for "is" relation
    is_forms = memory_manager.search_by_relation("is")

    assert len(is_forms) == 2  # 2 forms use "is"

    # Search for "are" relation
    are_forms = memory_manager.search_by_relation("are")

    assert len(are_forms) == 1  # 1 form uses "are"


# ============================================================================
# CONTEXT MANAGEMENT TESTS
# ============================================================================

def test_list_contexts(memory_manager, encoder, sample_logical_forms):
    """Test listing all contexts."""
    # Initially empty
    assert memory_manager.list_contexts() == []

    # Store forms
    for form in sample_logical_forms:
        encoder.add_embedding_to_form(form)
        memory_manager.store_form(form)

    # List contexts
    contexts = memory_manager.list_contexts()

    assert len(contexts) == 2
    assert "session_1" in contexts
    assert "session_2" in contexts
    assert contexts == sorted(contexts)  # Should be sorted


def test_clear_context(memory_manager, encoder, sample_logical_forms):
    """Test clearing all forms in a context."""
    # Store forms
    for form in sample_logical_forms:
        encoder.add_embedding_to_form(form)
        memory_manager.store_form(form)

    assert memory_manager.count_all_forms() == 3

    # Clear session_1
    deleted = memory_manager.clear_context("session_1")

    assert deleted == 2  # 2 forms were in session_1
    assert memory_manager.count_all_forms() == 1  # 1 form remains

    # Verify session_1 is empty
    session1_forms = memory_manager.get_forms_by_context("session_1")
    assert len(session1_forms) == 0

    # Verify session_2 still has its form
    session2_forms = memory_manager.get_forms_by_context("session_2")
    assert len(session2_forms) == 1


def test_clear_empty_context(memory_manager):
    """Test clearing a context with no forms."""
    deleted = memory_manager.clear_context("nonexistent")
    assert deleted == 0


def test_get_context_stats(memory_manager, encoder, sample_logical_forms):
    """Test getting statistics for a context."""
    # Store forms in session_1
    for form in sample_logical_forms[:2]:  # Only first 2 forms
        encoder.add_embedding_to_form(form)
        memory_manager.store_form(form)

    # Get stats
    stats = memory_manager.get_context_stats("session_1")

    assert stats["total_forms"] == 2
    assert stats["logical_types"]["universal_rule"] == 1
    assert stats["logical_types"]["ground_fact"] == 1
    assert stats["polarities"]["positive"] == 2
    assert 0.0 <= stats["avg_confidence"] <= 1.0


def test_get_context_stats_empty_context(memory_manager):
    """Test getting stats for empty context."""
    stats = memory_manager.get_context_stats("empty")

    assert stats["total_forms"] == 0
    assert stats["logical_types"] == {}
    assert stats["polarities"] == {}
    assert stats["avg_confidence"] == 0.0


def test_count_all_forms(memory_manager, encoder, sample_logical_forms):
    """Test counting total forms in database."""
    assert memory_manager.count_all_forms() == 0

    # Store forms
    for form in sample_logical_forms:
        encoder.add_embedding_to_form(form)
        memory_manager.store_form(form)

    assert memory_manager.count_all_forms() == 3


# ============================================================================
# PERSISTENCE TESTS
# ============================================================================

def test_persistent_storage_survives_restart(temp_dir, encoder, sample_logical_form):
    """Test that data persists across MemoryManager restarts."""
    # Create first manager and store form
    manager1 = MemoryManager(persist_directory=temp_dir, in_memory=False)
    encoder.add_embedding_to_form(sample_logical_form)
    form_id = manager1.store_form(sample_logical_form)

    assert manager1.count_all_forms() == 1

    # Create second manager (simulates restart)
    manager2 = MemoryManager(persist_directory=temp_dir, in_memory=False)

    # Data should still be there
    assert manager2.count_all_forms() == 1

    retrieved = manager2.retrieve_form(form_id)
    assert retrieved.source_text == sample_logical_form.source_text


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_workflow_integration(memory_manager, encoder):
    """
    Integration test: Full workflow from creation to consistency check preparation.

    Simulates the complete GLCS workflow:
    1. Create LogicalForms
    2. Add embeddings (Semantic Encoder)
    3. Store forms (Memory Manager)
    4. Query and retrieve forms
    5. Prepare for consistency checking
    """
    # Step 1: Create LogicalForms
    forms = [
        LogicalForm(
            context_id="session_123",
            logical_type=LogicalType.UNIVERSAL_RULE,
            subject=Entity(name="humans"),
            predicate=Relation(verb="are"),
            object=Entity(name="mortal"),
            polarity=Polarity.POSITIVE,
            source_text="All humans are mortal"
        ),
        LogicalForm(
            context_id="session_123",
            logical_type=LogicalType.GROUND_FACT,
            subject=Entity(name="socrates"),
            predicate=Relation(verb="is"),
            object=Entity(name="human"),
            polarity=Polarity.POSITIVE,
            source_text="Socrates is human"
        ),
        LogicalForm(
            context_id="session_123",
            logical_type=LogicalType.GROUND_FACT,
            subject=Entity(name="socrates"),
            predicate=Relation(verb="is"),
            object=Entity(name="mortal"),
            polarity=Polarity.POSITIVE,
            source_text="Therefore, Socrates is mortal"
        )
    ]

    # Step 2: Add embeddings
    encoder.add_embeddings_to_forms(forms)

    # Verify embeddings
    for form in forms:
        assert form.embedding is not None
        assert form.embedding.shape == (768,)

    # Step 3: Store forms
    form_ids = [memory_manager.store_form(form) for form in forms]
    assert len(form_ids) == 3

    # Step 4: Query and retrieve
    # Get all forms in context
    context_forms = memory_manager.get_forms_by_context("session_123")
    assert len(context_forms) == 3

    # Search for similar forms
    query_text = "Is Socrates mortal?"
    query_embedding = encoder.encode(query_text)
    similar = memory_manager.search_similar_forms(query_embedding, top_k=2)
    assert len(similar) == 2

    # Search by entity
    socrates_forms = memory_manager.search_by_entity("socrates")
    assert len(socrates_forms) == 2

    # Step 5: Get context stats for consistency checking
    stats = memory_manager.get_context_stats("session_123")
    assert stats["total_forms"] == 3
    assert stats["logical_types"]["universal_rule"] == 1
    assert stats["logical_types"]["ground_fact"] == 2

    # This data is now ready for Stage 1.3 (Consistency Checker)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_store_form_handles_chromadb_errors(memory_manager, encoder, sample_logical_form):
    """Test error handling when storing duplicate IDs."""
    encoder.add_embedding_to_form(sample_logical_form)

    # Store form successfully first
    form_id1 = memory_manager.store_form(sample_logical_form)
    assert form_id1 == sample_logical_form.form_id

    # ChromaDB allows storing same ID again (it updates instead of failing)
    # So this test verifies that it doesn't crash
    form_id2 = memory_manager.store_form(sample_logical_form)
    assert form_id2 == sample_logical_form.form_id

    # Verify form is still there
    retrieved = memory_manager.retrieve_form(form_id1)
    assert retrieved.form_id == sample_logical_form.form_id


def test_retrieve_form_handles_errors(memory_manager):
    """Test error handling during retrieval."""
    from uuid import uuid4

    # Try to retrieve non-existent form
    with pytest.raises(GLCSMemoryError, match="Form not found"):
        memory_manager.retrieve_form(uuid4())


# ============================================================================
# RECONSTRUCTION TESTS
# ============================================================================

def test_form_reconstruction_preserves_data(memory_manager, encoder, sample_logical_form):
    """Test that LogicalForm reconstruction preserves all data."""
    encoder.add_embedding_to_form(sample_logical_form)
    original_id = sample_logical_form.form_id
    original_timestamp = sample_logical_form.timestamp
    original_embedding = sample_logical_form.embedding.copy()

    # Store and retrieve
    memory_manager.store_form(sample_logical_form)
    retrieved = memory_manager.retrieve_form(original_id)

    # Verify all fields match
    assert retrieved.form_id == original_id
    assert retrieved.context_id == sample_logical_form.context_id
    assert retrieved.timestamp == original_timestamp
    assert retrieved.logical_type == sample_logical_form.logical_type
    assert retrieved.subject.name == sample_logical_form.subject.name
    assert retrieved.predicate.verb == sample_logical_form.predicate.verb
    assert retrieved.object.name == sample_logical_form.object.name
    assert retrieved.polarity == sample_logical_form.polarity
    assert retrieved.confidence_score == sample_logical_form.confidence_score
    assert retrieved.source_text == sample_logical_form.source_text
    assert np.allclose(retrieved.embedding, original_embedding)


# ============================================================================
# LOSSLESS ROUND-TRIP TESTS (#41)
# ============================================================================

def test_round_trip_preserves_entity_ids(memory_manager, encoder):
    """store→retrieve must keep entity_id for subject and object unchanged."""
    form = LogicalForm(
        context_id="ctx",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="alice", entity_type="person"),
        predicate=Relation(verb="knows"),
        object=Entity(name="bob", entity_type="person"),
        polarity=Polarity.POSITIVE,
        source_text="Alice knows Bob",
    )
    encoder.add_embedding_to_form(form)
    subject_id = form.subject.entity_id
    object_id = form.object.entity_id

    form_id = memory_manager.store_form(form)
    retrieved = memory_manager.retrieve_form(form_id)

    assert retrieved.subject.entity_id == subject_id
    assert retrieved.object.entity_id == object_id


def test_round_trip_preserves_relation_id(memory_manager, encoder):
    """store→retrieve must keep relation_id on the predicate unchanged."""
    form = LogicalForm(
        context_id="ctx",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is", relation_type="property"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Socrates is mortal",
    )
    encoder.add_embedding_to_form(form)
    predicate_id = form.predicate.relation_id

    form_id = memory_manager.store_form(form)
    retrieved = memory_manager.retrieve_form(form_id)

    assert retrieved.predicate.relation_id == predicate_id


def test_round_trip_preserves_relation_type(memory_manager, encoder):
    """store→retrieve must restore predicate.relation_type."""
    form = LogicalForm(
        context_id="ctx",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="earth"),
        predicate=Relation(verb="orbits", relation_type="spatial"),
        object=Entity(name="sun"),
        polarity=Polarity.POSITIVE,
        source_text="Earth orbits Sun",
    )
    encoder.add_embedding_to_form(form)
    form_id = memory_manager.store_form(form)
    retrieved = memory_manager.retrieve_form(form_id)

    assert retrieved.predicate.relation_type == "spatial"


def test_round_trip_preserves_form_metadata(memory_manager, encoder):
    """store→retrieve must restore form-level metadata dict."""
    form = LogicalForm(
        context_id="ctx",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="plato"),
        predicate=Relation(verb="is"),
        object=Entity(name="philosopher"),
        polarity=Polarity.POSITIVE,
        source_text="Plato is a philosopher",
        metadata={"source": "wikipedia", "confidence": 0.97},
    )
    encoder.add_embedding_to_form(form)
    form_id = memory_manager.store_form(form)
    retrieved = memory_manager.retrieve_form(form_id)

    assert retrieved.metadata == {"source": "wikipedia", "confidence": 0.97}


def test_round_trip_preserves_entity_metadata(memory_manager, encoder):
    """store→retrieve must restore metadata on subject and object entities."""
    form = LogicalForm(
        context_id="ctx",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="aristotle", metadata={"era": "ancient", "born": -384}),
        predicate=Relation(verb="studied_under"),
        object=Entity(name="plato", metadata={"role": "teacher"}),
        polarity=Polarity.POSITIVE,
        source_text="Aristotle studied under Plato",
    )
    encoder.add_embedding_to_form(form)
    form_id = memory_manager.store_form(form)
    retrieved = memory_manager.retrieve_form(form_id)

    assert retrieved.subject.metadata == {"era": "ancient", "born": -384}
    assert retrieved.object.metadata == {"role": "teacher"}
