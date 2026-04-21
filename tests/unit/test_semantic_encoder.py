"""
Unit tests for Semantic Encoder (Stage 1.1).

Tests the SemanticEncoder class which generates 768-dimensional embeddings
using sentence-transformers.

Test Coverage:
    - Single text encoding
    - Batch text encoding
    - Embedding dimension validation
    - LogicalForm integration
    - Cosine similarity computation
    - Error handling
    - Model caching
"""

import pytest
import numpy as np

from glcs.core.semantic_encoder import SemanticEncoder
from glcs.core.models import (
    LogicalForm,
    Entity,
    Relation,
    LogicalType,
    Polarity
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_texts():
    """Sample texts for testing encoding."""
    return [
        "All humans are mortal",
        "Socrates is human",
        "Socrates is mortal",
        "The sky is blue",
        "Cats are animals"
    ]


# ============================================================================
# BASIC ENCODING TESTS
# ============================================================================

def test_encoder_initialization():
    """Test that encoder initializes with default model."""
    encoder = SemanticEncoder()
    assert encoder.model_name == "all-mpnet-base-v2"
    assert encoder.model is not None


def test_encoder_custom_model():
    """Test encoder with custom model name."""
    encoder = SemanticEncoder(model_name="all-mpnet-base-v2")
    assert encoder.model_name == "all-mpnet-base-v2"


def test_encode_single_text(encoder):
    """Test encoding a single text string."""
    text = "All humans are mortal"
    embedding = encoder.encode(text)

    # Check type and shape
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (768,)
    assert embedding.dtype == np.float32


def test_encode_returns_different_embeddings_for_different_texts(encoder):
    """Test that different texts produce different embeddings."""
    emb1 = encoder.encode("All humans are mortal")
    emb2 = encoder.encode("The sky is blue")

    # Embeddings should not be identical
    assert not np.allclose(emb1, emb2, rtol=0.01)


def test_encode_returns_similar_embeddings_for_similar_texts(encoder):
    """Test that similar texts produce similar embeddings."""
    emb1 = encoder.encode("All humans are mortal")
    emb2 = encoder.encode("Every person is mortal")

    # Calculate cosine similarity
    similarity = encoder.cosine_similarity(emb1, emb2)

    # Similar texts should have high similarity (> 0.5)
    assert similarity > 0.5


def test_encode_normalization(encoder):
    """Test that normalized embeddings have unit length."""
    embedding = encoder.encode("Test text", normalize=True)

    # Calculate L2 norm
    norm = np.linalg.norm(embedding)

    # Should be very close to 1.0 (unit vector)
    assert abs(norm - 1.0) < 0.01


def test_encode_without_normalization(encoder):
    """Test encoding without normalization."""
    embedding = encoder.encode("Test text", normalize=False)

    # Should still be 768 dimensions
    assert embedding.shape == (768,)

    # But norm may not be 1.0
    norm = np.linalg.norm(embedding)
    # Just check it's a reasonable value (not zero, not infinite)
    assert 0.1 < norm < 100.0


# ============================================================================
# BATCH ENCODING TESTS
# ============================================================================

def test_encode_batch(encoder, sample_texts):
    """Test batch encoding of multiple texts."""
    embeddings = encoder.encode_batch(sample_texts)

    # Check we got the right number of embeddings
    assert len(embeddings) == len(sample_texts)

    # Check each embedding has correct shape
    for emb in embeddings:
        assert isinstance(emb, np.ndarray)
        assert emb.shape == (768,)
        assert emb.dtype == np.float32


def test_encode_batch_produces_same_results_as_single(encoder):
    """Test that batch encoding produces same results as individual encoding."""
    texts = ["Text one", "Text two", "Text three"]

    # Encode individually
    individual_embs = [encoder.encode(text) for text in texts]

    # Encode in batch
    batch_embs = encoder.encode_batch(texts)

    # Results should be identical (or very close due to floating point)
    for ind_emb, batch_emb in zip(individual_embs, batch_embs):
        assert np.allclose(ind_emb, batch_emb, rtol=1e-5, atol=1e-7)


def test_encode_batch_with_custom_batch_size(encoder):
    """Test batch encoding with custom batch size."""
    texts = ["Text " + str(i) for i in range(10)]
    embeddings = encoder.encode_batch(texts, batch_size=3)

    assert len(embeddings) == 10
    for emb in embeddings:
        assert emb.shape == (768,)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_encode_empty_text_raises_error(encoder):
    """Test that encoding empty text raises ValueError."""
    with pytest.raises(ValueError, match="Cannot encode empty text"):
        encoder.encode("")


def test_encode_whitespace_only_raises_error(encoder):
    """Test that encoding whitespace-only text raises ValueError."""
    with pytest.raises(ValueError, match="Cannot encode empty text"):
        encoder.encode("   ")


def test_encode_batch_empty_list_raises_error(encoder):
    """Test that encoding empty list raises ValueError."""
    with pytest.raises(ValueError, match="Cannot encode empty list"):
        encoder.encode_batch([])


def test_encode_batch_with_empty_text_raises_error(encoder):
    """Test that batch encoding with an empty text raises ValueError."""
    texts = ["Valid text", "", "Another valid text"]

    with pytest.raises(ValueError, match="Text at index 1 is empty"):
        encoder.encode_batch(texts)


# ============================================================================
# LOGICALFORM INTEGRATION TESTS
# ============================================================================

def test_add_embedding_to_form(encoder, sample_logical_form):
    """Test adding embedding to a LogicalForm."""
    # Initially no embedding
    assert sample_logical_form.embedding is None

    # Add embedding
    result = encoder.add_embedding_to_form(sample_logical_form)

    # Check embedding was added
    assert sample_logical_form.embedding is not None
    assert sample_logical_form.embedding.shape == (768,)

    # Check it returns the same form
    assert result is sample_logical_form


def test_add_embedding_to_form_uses_source_text(encoder):
    """Test that embedding is based on source_text field."""
    form = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Socrates is mortal"
    )

    # Add embedding
    encoder.add_embedding_to_form(form)

    # Encode the source text directly
    direct_embedding = encoder.encode("Socrates is mortal")

    # They should be identical
    assert np.allclose(form.embedding, direct_embedding, rtol=1e-5, atol=1e-7)


def test_add_embeddings_to_forms_batch(encoder):
    """Test adding embeddings to multiple forms efficiently."""
    forms = [
        LogicalForm(
            context_id="test",
            logical_type=LogicalType.UNIVERSAL_RULE,
            subject=Entity(name="humans"),
            predicate=Relation(verb="are"),
            object=Entity(name="mortal"),
            polarity=Polarity.POSITIVE,
            source_text="All humans are mortal"
        ),
        LogicalForm(
            context_id="test",
            logical_type=LogicalType.GROUND_FACT,
            subject=Entity(name="socrates"),
            predicate=Relation(verb="is"),
            object=Entity(name="human"),
            polarity=Polarity.POSITIVE,
            source_text="Socrates is human"
        ),
        LogicalForm(
            context_id="test",
            logical_type=LogicalType.GROUND_FACT,
            subject=Entity(name="socrates"),
            predicate=Relation(verb="is"),
            object=Entity(name="mortal"),
            polarity=Polarity.POSITIVE,
            source_text="Socrates is mortal"
        )
    ]

    # Add embeddings in batch
    result = encoder.add_embeddings_to_forms(forms)

    # Check all forms have embeddings
    assert len(result) == 3
    for form in forms:
        assert form.embedding is not None
        assert form.embedding.shape == (768,)


def test_add_embeddings_to_forms_empty_list(encoder):
    """Test that adding embeddings to empty list returns empty list."""
    result = encoder.add_embeddings_to_forms([])
    assert result == []


def test_logical_form_validates_embedding_dimension(encoder):
    """LogicalForm accepts any 1D embedding — dimension is not hardcoded (#37)."""
    form = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="test"),
        predicate=Relation(verb="is"),
        polarity=Polarity.POSITIVE,
        source_text="Test"
    )

    # Non-768 1D arrays are now valid — the encoder, not the model, enforces dimension
    form.embedding = np.random.rand(512)
    assert form.embedding.shape == (512,)

    # Multi-dimensional arrays are still rejected
    with pytest.raises(ValueError):
        form.embedding = np.random.rand(768, 1)


# ============================================================================
# COSINE SIMILARITY TESTS
# ============================================================================

def test_cosine_similarity_identical_texts(encoder):
    """Test that identical texts have similarity of 1.0."""
    text = "All humans are mortal"
    emb1 = encoder.encode(text)
    emb2 = encoder.encode(text)

    similarity = encoder.cosine_similarity(emb1, emb2)

    # Should be very close to 1.0
    assert abs(similarity - 1.0) < 0.01


def test_cosine_similarity_similar_texts(encoder):
    """Test similarity between semantically similar texts."""
    emb1 = encoder.encode("All humans are mortal")
    emb2 = encoder.encode("Every person is mortal")

    similarity = encoder.cosine_similarity(emb1, emb2)

    # Should be high (> 0.5) but not perfect
    assert 0.5 < similarity < 1.0


def test_cosine_similarity_unrelated_texts(encoder):
    """Test similarity between unrelated texts."""
    emb1 = encoder.encode("All humans are mortal")
    emb2 = encoder.encode("The sky is blue")

    similarity = encoder.cosine_similarity(emb1, emb2)

    # Should be low (< 0.3)
    assert similarity < 0.3


def test_cosine_similarity_different_shapes_raises_error(encoder):
    """Test that comparing embeddings of different shapes raises error."""
    emb1 = np.random.rand(768)
    emb2 = np.random.rand(512)

    with pytest.raises(ValueError, match="must have same shape"):
        encoder.cosine_similarity(emb1, emb2)


def test_cosine_similarity_range(encoder, sample_texts):
    """Test that cosine similarity is always between -1 and 1."""
    embeddings = encoder.encode_batch(sample_texts)

    # Compare all pairs
    for i, emb1 in enumerate(embeddings):
        for j, emb2 in enumerate(embeddings):
            similarity = encoder.cosine_similarity(emb1, emb2)
            # Allow small floating point tolerance
            assert -1.01 <= similarity <= 1.01


# ============================================================================
# MODEL CACHING TESTS
# ============================================================================

def test_model_cache_reuses_model():
    """Test that multiple encoders reuse the same cached model."""
    SemanticEncoder.clear_model_cache()

    encoder1 = SemanticEncoder()
    encoder2 = SemanticEncoder()

    # Should be the exact same model object (cached)
    assert encoder1.model is encoder2.model


def test_model_cache_different_models():
    """Test that different model names don't share cache."""
    SemanticEncoder.clear_model_cache()

    encoder1 = SemanticEncoder("all-mpnet-base-v2")

    # Note: We can't easily test with a different model name
    # because it would need to download another model
    # So we'll just verify the cache key is set correctly
    assert SemanticEncoder._cached_model_name == "all-mpnet-base-v2"


def test_clear_model_cache():
    """Test that clearing cache removes cached model."""
    encoder = SemanticEncoder()
    assert SemanticEncoder._model_cache is not None

    SemanticEncoder.clear_model_cache()
    assert SemanticEncoder._model_cache is None
    assert SemanticEncoder._cached_model_name is None


# ============================================================================
# INTEGRATION TEST
# ============================================================================

def test_full_workflow_integration(encoder):
    """
    Integration test: Create LogicalForms, add embeddings, compute similarities.

    This simulates the full workflow:
    1. Parse natural language to LogicalForm (simulated)
    2. Add embeddings to forms
    3. Compare forms using cosine similarity
    """
    # Step 1: Create LogicalForms (simulating parser output)
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

    # Verify all have embeddings
    for form in forms:
        assert form.embedding is not None
        assert form.embedding.shape == (768,)

    # Step 3: Compare embeddings
    # forms[0] and forms[2] both mention mortality - should be somewhat similar
    similarity = encoder.cosine_similarity(forms[0].embedding, forms[2].embedding)
    assert similarity > 0.3  # At least moderately related

    # forms[1] and forms[2] both mention Socrates - should be similar
    similarity = encoder.cosine_similarity(forms[1].embedding, forms[2].embedding)
    assert similarity > 0.4  # Should be related


# ============================================================================
# DIMENSION VALIDATION TESTS
# ============================================================================

def test_embedding_dimension_exactly_768(encoder):
    """Test that all embeddings are exactly 768 dimensions."""
    texts = ["Short", "A longer text string", "An even longer text string with more words"]

    for text in texts:
        embedding = encoder.encode(text)
        assert embedding.shape == (768,), f"Expected (768,), got {embedding.shape}"


def test_batch_embedding_dimensions_all_768(encoder, sample_texts):
    """Test that batch encoding produces all 768-dim embeddings."""
    embeddings = encoder.encode_batch(sample_texts)

    for i, emb in enumerate(embeddings):
        assert emb.shape == (768,), f"Embedding {i} has shape {emb.shape}, expected (768,)"


# ============================================================================
# DETERMINISM TESTS
# ============================================================================

def test_encode_is_deterministic(encoder):
    """Test that encoding the same text twice produces identical results."""
    text = "All humans are mortal"

    emb1 = encoder.encode(text)
    emb2 = encoder.encode(text)

    # Should be identical (bit-for-bit)
    assert np.array_equal(emb1, emb2)


def test_batch_encode_is_deterministic(encoder):
    """Test that batch encoding is deterministic."""
    texts = ["Text one", "Text two", "Text three"]

    embs1 = encoder.encode_batch(texts)
    embs2 = encoder.encode_batch(texts)

    for e1, e2 in zip(embs1, embs2):
        assert np.array_equal(e1, e2)
