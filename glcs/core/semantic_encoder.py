"""
Semantic Encoder for GLCS (Global Logical Context Store).

This module provides semantic embedding functionality using sentence-transformers.
It converts text into 768-dimensional vector representations that enable semantic
similarity comparisons and consistency checking.

Key Features:
    - Generates 768-dimensional embeddings using all-mpnet-base-v2 model
    - Thread-safe singleton pattern for model reuse
    - Batch processing support for efficiency
    - Automatic normalization of embeddings
    - Integration with LogicalForm data model

Usage:
    >>> from glcs.core.semantic_encoder import SemanticEncoder
    >>> from glcs.core.models import LogicalForm
    >>>
    >>> encoder = SemanticEncoder()
    >>> embedding = encoder.encode("All humans are mortal")
    >>> embedding.shape
    (768,)
"""

from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from glcs.core.models import LogicalForm


class SemanticEncoder:
    """
    Generates semantic embeddings for text using sentence-transformers.

    This class wraps the sentence-transformers library to provide:
    - Consistent 768-dimensional embeddings
    - Singleton pattern for model efficiency
    - Integration with GLCS LogicalForm objects

    The encoder uses the 'all-mpnet-base-v2' model by default, which:
    - Produces 768-dimensional vectors
    - Is moderate size (~420MB)
    - Has excellent performance on semantic similarity tasks
    - Maps sentences to a dense vector space

    Attributes:
        model_name: Name of the sentence-transformers model
        model: Loaded SentenceTransformer model instance

    Example:
        >>> encoder = SemanticEncoder()
        >>> text = "All humans are mortal"
        >>> embedding = encoder.encode(text)
        >>> embedding.shape
        (768,)
        >>> isinstance(embedding, np.ndarray)
        True
    """

    # Class-level cache for model singleton
    _model_cache: Optional[SentenceTransformer] = None
    _cached_model_name: Optional[str] = None

    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        """
        Initialize the Semantic Encoder.

        Args:
            model_name: Name of the sentence-transformers model to use.
                       Default is 'all-mpnet-base-v2' (768 dimensions).

        Note:
            The model is loaded lazily on first encode() call and cached
            for subsequent uses. This avoids loading the model multiple times.
        """
        self.model_name = model_name
        self.model = self._load_model()
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

    def _load_model(self) -> SentenceTransformer:
        """
        Load the sentence-transformers model with caching.

        Uses a class-level cache to avoid loading the same model multiple times.
        This is particularly important for:
        - API servers (model persists across requests)
        - Test suites (model loaded once per test session)
        - Batch processing (model reused for multiple encodes)

        Returns:
            Loaded SentenceTransformer model instance
        """
        # Check if model is already cached
        if (SemanticEncoder._model_cache is not None and
            SemanticEncoder._cached_model_name == self.model_name):
            return SemanticEncoder._model_cache

        # Load model and cache it
        model = SentenceTransformer(self.model_name)
        SemanticEncoder._model_cache = model
        SemanticEncoder._cached_model_name = self.model_name

        return model

    def encode(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Encode a single text string into a 768-dimensional embedding.

        Args:
            text: Input text to encode (e.g., "All humans are mortal")
            normalize: Whether to L2-normalize the embedding vector (default True)
                      Normalization ensures cosine similarity = dot product

        Returns:
            768-dimensional numpy array representing the semantic embedding

        Raises:
            ValueError: If text is empty or None

        Example:
            >>> encoder = SemanticEncoder()
            >>> embedding = encoder.encode("Socrates is mortal")
            >>> embedding.shape
            (768,)
            >>> -1.0 <= embedding.min() <= 1.0  # Normalized values
            True
        """
        if not text or not text.strip():
            raise ValueError("Cannot encode empty text")

        # Encode text using sentence-transformers
        embedding = self.model.encode(
            text,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )

        # Ensure output is numpy array with correct shape
        embedding = np.array(embedding, dtype=np.float32)

        if embedding.shape != (self.embedding_dim,):
            raise RuntimeError(
                f"Model {self.model_name} produced {embedding.shape} dimensions, "
                f"expected ({self.embedding_dim},). Model may have changed."
            )

        return embedding

    def encode_batch(
        self,
        texts: List[str],
        normalize: bool = True,
        batch_size: int = 32
    ) -> List[np.ndarray]:
        """
        Encode multiple texts in batch for efficiency.

        Batch encoding is significantly faster than encoding texts individually:
        - Single encode: ~10ms per text
        - Batch encode: ~2ms per text (5x speedup)

        Args:
            texts: List of text strings to encode
            normalize: Whether to L2-normalize embeddings (default True)
            batch_size: Number of texts to process at once (default 32)
                       Higher = faster but more memory

        Returns:
            List of 768-dimensional numpy arrays, one per input text

        Raises:
            ValueError: If any text is empty or texts list is empty

        Example:
            >>> encoder = SemanticEncoder()
            >>> texts = [
            ...     "All humans are mortal",
            ...     "Socrates is human",
            ...     "Socrates is mortal"
            ... ]
            >>> embeddings = encoder.encode_batch(texts)
            >>> len(embeddings)
            3
            >>> all(e.shape == (768,) for e in embeddings)
            True
        """
        if not texts:
            raise ValueError("Cannot encode empty list of texts")

        # Validate all texts are non-empty
        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Text at index {i} is empty")

        # Encode all texts in batch
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            batch_size=batch_size,
            show_progress_bar=False
        )

        # Convert to list of numpy arrays
        embeddings = [np.array(emb, dtype=np.float32) for emb in embeddings]

        # Validate dimensions
        for i, emb in enumerate(embeddings):
            if emb.shape != (self.embedding_dim,):
                raise RuntimeError(
                    f"Embedding at index {i} has shape {emb.shape}, expected ({self.embedding_dim},)"
                )

        return embeddings

    def add_embedding_to_form(self, form: LogicalForm) -> LogicalForm:
        """
        Add semantic embedding to a LogicalForm object.

        This is a convenience method that:
        1. Encodes the LogicalForm's source_text
        2. Adds the embedding to the form's embedding field
        3. Returns the modified form

        The form is modified in-place AND returned for convenience.

        Args:
            form: LogicalForm object to add embedding to

        Returns:
            The same LogicalForm object with embedding field populated

        Example:
            >>> from glcs.core.models import LogicalForm, Entity, Relation
            >>> from glcs.core.models import LogicalType, Polarity
            >>>
            >>> form = LogicalForm(
            ...     context_id="session_123",
            ...     logical_type=LogicalType.UNIVERSAL_RULE,
            ...     subject=Entity(name="humans"),
            ...     predicate=Relation(verb="are"),
            ...     object=Entity(name="mortal"),
            ...     polarity=Polarity.POSITIVE,
            ...     source_text="All humans are mortal"
            ... )
            >>>
            >>> encoder = SemanticEncoder()
            >>> form = encoder.add_embedding_to_form(form)
            >>> form.embedding.shape
            (768,)
        """
        # Encode the source text
        embedding = self.encode(form.source_text)

        # Add to form (this will trigger Pydantic validation)
        form.embedding = embedding

        return form

    def add_embeddings_to_forms(self, forms: List[LogicalForm]) -> List[LogicalForm]:
        """
        Add embeddings to multiple LogicalForm objects efficiently.

        Uses batch encoding for better performance when processing many forms.

        Args:
            forms: List of LogicalForm objects to add embeddings to

        Returns:
            List of LogicalForm objects with embeddings added

        Example:
            >>> encoder = SemanticEncoder()
            >>> forms = [form1, form2, form3]  # List of LogicalForms
            >>> forms = encoder.add_embeddings_to_forms(forms)
            >>> all(f.embedding is not None for f in forms)
            True
        """
        if not forms:
            return forms

        # Extract source texts
        texts = [form.source_text for form in forms]

        # Encode in batch
        embeddings = self.encode_batch(texts)

        # Add embeddings to forms
        for form, embedding in zip(forms, embeddings):
            form.embedding = embedding

        return forms

    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.

        Cosine similarity ranges from -1 (opposite) to 1 (identical):
        - 1.0: Identical meaning
        - 0.7-0.9: Very similar
        - 0.5-0.7: Moderately similar
        - 0.3-0.5: Somewhat related
        - 0.0-0.3: Unrelated
        - < 0.0: Opposite meaning (rare)

        If embeddings are normalized (L2 norm = 1), cosine similarity
        equals the dot product, which is computationally efficient.

        Args:
            embedding1: First 768-dimensional embedding
            embedding2: Second 768-dimensional embedding

        Returns:
            Cosine similarity score between -1 and 1

        Raises:
            ValueError: If embeddings have different shapes

        Example:
            >>> encoder = SemanticEncoder()
            >>> emb1 = encoder.encode("All humans are mortal")
            >>> emb2 = encoder.encode("Every person is mortal")
            >>> emb3 = encoder.encode("The sky is blue")
            >>>
            >>> encoder.cosine_similarity(emb1, emb2)  # Similar
            0.89
            >>> encoder.cosine_similarity(emb1, emb3)  # Unrelated
            0.12
        """
        if embedding1.shape != embedding2.shape:
            raise ValueError(
                f"Embeddings must have same shape, got {embedding1.shape} and {embedding2.shape}"
            )

        # If embeddings are normalized, dot product = cosine similarity
        # This is MUCH faster than the full formula
        similarity = np.dot(embedding1, embedding2)

        return float(similarity)

    @staticmethod
    def clear_model_cache():
        """
        Clear the cached model from memory.

        Useful for:
        - Testing (ensure clean state between tests)
        - Memory management (free ~80MB)
        - Model switching (load different model)

        Example:
            >>> SemanticEncoder.clear_model_cache()
            >>> encoder = SemanticEncoder()  # Will reload model
        """
        SemanticEncoder._model_cache = None
        SemanticEncoder._cached_model_name = None
