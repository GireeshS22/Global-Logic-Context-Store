"""
Memory Manager for GLCS (Global Logical Context Store).

This module provides persistent vector storage for LogicalForm objects using ChromaDB.
It enables efficient storage, retrieval, and similarity search of logical statements.

Key Features:
    - Persistent storage with ChromaDB vector database
    - CRUD operations for LogicalForm objects
    - Semantic similarity search
    - Context-based filtering and management
    - Entity and relation-based queries
    - In-memory mode for testing

Usage:
    >>> from glcs.core.memory_manager import MemoryManager
    >>> from glcs.core.models import LogicalForm
    >>>
    >>> manager = MemoryManager()
    >>> form_id = manager.store_form(form)
    >>> retrieved = manager.retrieve_form(form_id)
"""

from typing import Dict, List, Optional
from uuid import UUID

import chromadb
from chromadb.config import Settings
import numpy as np

from glcs.core.models import LogicalForm
from glcs.utils.exceptions import GLCSMemoryError
from glcs.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryManager:
    """
    Manages persistent storage of LogicalForm objects using ChromaDB.

    The MemoryManager provides a vector database interface for storing and
    retrieving LogicalForm objects. It uses ChromaDB as the backend, which
    enables efficient similarity search based on semantic embeddings.

    Features:
        - CRUD operations (Create, Read, Update, Delete)
        - Semantic similarity search using embeddings
        - Context-based filtering
        - Entity and relation-based queries
        - Persistent storage with automatic persistence
        - In-memory mode for testing

    Attributes:
        collection_name: Name of the ChromaDB collection
        client: ChromaDB client instance
        collection: ChromaDB collection for storing forms

    Example:
        >>> manager = MemoryManager()
        >>>
        >>> # Store a form
        >>> form_id = manager.store_form(form)
        >>>
        >>> # Retrieve by ID
        >>> form = manager.retrieve_form(form_id)
        >>>
        >>> # Search by similarity
        >>> similar = manager.search_similar_forms(form.embedding, top_k=5)
        >>>
        >>> # Get all forms in a context
        >>> context_forms = manager.get_forms_by_context("session_123")
    """

    def __init__(
        self,
        collection_name: str = "logical_forms",
        persist_directory: Optional[str] = "./chroma_db",
        in_memory: bool = False
    ):
        """
        Initialize the Memory Manager.

        Args:
            collection_name: Name of the ChromaDB collection (default: "logical_forms")
            persist_directory: Directory for persistent storage (default: "./chroma_db")
                             Ignored if in_memory=True
            in_memory: If True, use in-memory storage for testing (default: False)

        Raises:
            GLCSMemoryError: If ChromaDB initialization fails
        """
        self.collection_name = collection_name
        self.in_memory = in_memory

        try:
            if in_memory:
                # In-memory client for testing
                self.client = chromadb.Client()
                logger.info("Initialized in-memory MemoryManager")
            else:
                # Persistent client for production
                self.client = chromadb.PersistentClient(path=persist_directory)
                logger.info(f"Initialized persistent MemoryManager at {persist_directory}")

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "GLCS logical forms with embeddings"}
            )

            logger.info(f"Using collection '{collection_name}' with {self.collection.count()} forms")

        except Exception as e:
            raise GLCSMemoryError(
                f"Failed to initialize MemoryManager: {str(e)} "
                f"(collection_name: {collection_name})"
            )

    # ========================================================================
    # CRUD OPERATIONS
    # ========================================================================

    def store_form(self, form: LogicalForm) -> UUID:
        """
        Store a LogicalForm in the vector database.

        The form must have an embedding (768-dim vector). If not, use
        SemanticEncoder to add one first.

        Args:
            form: LogicalForm to store (must have embedding)

        Returns:
            UUID of the stored form (form.form_id)

        Raises:
            GLCSMemoryError: If form has no embedding or storage fails

        Example:
            >>> from glcs.core.semantic_encoder import SemanticEncoder
            >>> encoder = SemanticEncoder()
            >>> encoder.add_embedding_to_form(form)
            >>> form_id = manager.store_form(form)
        """
        if form.embedding is None:
            raise GLCSMemoryError(
                f"Cannot store form without embedding. Use SemanticEncoder first. "
                f"(form_id: {form.form_id})"
            )

        try:
            metadata = self._build_metadata(form)

            # Store in ChromaDB
            self.collection.add(
                ids=[str(form.form_id)],
                embeddings=[form.embedding.tolist()],
                metadatas=[metadata],
                documents=[form.source_text]
            )

            logger.debug(f"Stored form {form.form_id} in context '{form.context_id}'")
            return form.form_id

        except Exception as e:
            raise GLCSMemoryError(
                f"Failed to store form: {str(e)}",
                context={"form_id": str(form.form_id)}
            )

    def retrieve_form(self, form_id: UUID) -> LogicalForm:
        """
        Retrieve a LogicalForm by its ID.

        Args:
            form_id: UUID of the form to retrieve

        Returns:
            LogicalForm object

        Raises:
            GLCSMemoryError: If form not found or retrieval fails

        Example:
            >>> form = manager.retrieve_form(form_id)
            >>> print(form.source_text)
        """
        try:
            result = self.collection.get(
                ids=[str(form_id)],
                include=["embeddings", "metadatas", "documents"]
            )

            if not result["ids"]:
                raise GLCSMemoryError(f"Form not found: {form_id} (form_id: {form_id})")

            # Reconstruct LogicalForm from stored data
            form = self._reconstruct_form(
                form_id=UUID(result["ids"][0]),
                embedding=np.array(result["embeddings"][0]),
                metadata=result["metadatas"][0],
                source_text=result["documents"][0]
            )

            logger.debug(f"Retrieved form {form_id}")
            return form

        except GLCSMemoryError:
            raise
        except Exception as e:
            raise GLCSMemoryError(f"Failed to retrieve form: {str(e)} (form_id: {form_id})")

    def update_form(self, form_id: UUID, form: LogicalForm) -> None:
        """
        Update an existing LogicalForm.

        Note: This replaces the entire form. The form_id in the form object
        is ignored - the form_id parameter determines which form to update.

        Args:
            form_id: UUID of the form to update
            form: New LogicalForm data (must have embedding)

        Raises:
            GLCSMemoryError: If form not found or update fails

        Example:
            >>> form.confidence_score = 0.95
            >>> manager.update_form(form_id, form)
        """
        # Check if form exists
        try:
            self.retrieve_form(form_id)
        except GLCSMemoryError:
            raise GLCSMemoryError(f"Cannot update non-existent form: {form_id} (form_id: {form_id})")

        if form.embedding is None:
            raise GLCSMemoryError(f"Cannot update form without embedding. (form_id: {form_id})")

        try:
            metadata = self._build_metadata(form)

            # Update in ChromaDB
            self.collection.update(
                ids=[str(form_id)],
                embeddings=[form.embedding.tolist()],
                metadatas=[metadata],
                documents=[form.source_text]
            )

            logger.debug(f"Updated form {form_id}")

        except Exception as e:
            raise GLCSMemoryError(f"Failed to update form: {str(e)} (form_id: {form_id})")

    def delete_form(self, form_id: UUID) -> bool:
        """
        Delete a LogicalForm from storage.

        Args:
            form_id: UUID of the form to delete

        Returns:
            True if deleted, False if form was not found (#74)

        Raises:
            GLCSMemoryError: If deletion fails

        Example:
            >>> deleted = manager.delete_form(form_id)
            >>> if deleted:
            ...     print("Deleted successfully")
        """
        try:
            # Check if it exists first because ChromaDB.delete is silent (#74)
            result = self.collection.get(ids=[str(form_id)], include=[])
            if not result["ids"]:
                logger.debug(f"Form {form_id} not found for deletion")
                return False

            self.collection.delete(ids=[str(form_id)])
            logger.debug(f"Deleted form {form_id}")
            return True

        except Exception as e:
            raise GLCSMemoryError(f"Failed to delete form: {str(e)} (form_id: {form_id})")

    # ========================================================================
    # QUERY OPERATIONS
    # ========================================================================

    def get_forms_by_context(self, context_id: str) -> List[LogicalForm]:
        """
        Retrieve all LogicalForms in a specific context.

        Args:
            context_id: Context/session ID to filter by

        Returns:
            List of LogicalForm objects in the context

        Example:
            >>> forms = manager.get_forms_by_context("session_123")
            >>> print(f"Found {len(forms)} forms in session_123")
        """
        try:
            result = self.collection.get(
                where={"context_id": context_id},
                include=["embeddings", "metadatas", "documents"]
            )

            forms = [
                self._reconstruct_form(
                    form_id=UUID(form_id),
                    embedding=np.array(embedding),
                    metadata=metadata,
                    source_text=document
                )
                for form_id, embedding, metadata, document in zip(
                    result["ids"],
                    result["embeddings"],
                    result["metadatas"],
                    result["documents"]
                )
            ]

            logger.debug(f"Retrieved {len(forms)} forms from context '{context_id}'")
            return forms

        except Exception as e:
            raise GLCSMemoryError(f"Failed to get forms by context: {str(e)} (context_id: {context_id})")

    def search_similar_forms(
        self,
        embedding: np.ndarray,
        top_k: int = 5,
        context_id: Optional[str] = None
    ) -> List[LogicalForm]:
        """
        Search for semantically similar LogicalForms.

        Uses cosine similarity on embeddings to find the most similar forms.

        Args:
            embedding: 768-dim query embedding
            top_k: Number of results to return (default: 5)
            context_id: Optional context filter (default: search all contexts)

        Returns:
            List of similar LogicalForms, ordered by similarity (most similar first)

        Example:
            >>> similar = manager.search_similar_forms(form.embedding, top_k=10)
            >>> for sim_form in similar:
            ...     print(f"Similar: {sim_form.source_text}")
        """
        if embedding.shape != (768,):
            raise GLCSMemoryError(f"Embedding must be 768-dimensional, got {embedding.shape} (embedding_shape: {embedding.shape})")

        try:
            # Build query
            where = {"context_id": context_id} if context_id else None

            result = self.collection.query(
                query_embeddings=[embedding.tolist()],
                n_results=top_k,
                where=where,
                include=["embeddings", "metadatas", "documents"]
            )

            # ChromaDB returns results in batches (even for single query)
            forms = [
                self._reconstruct_form(
                    form_id=UUID(form_id),
                    embedding=np.array(emb),
                    metadata=meta,
                    source_text=doc
                )
                for form_id, emb, meta, doc in zip(
                    result["ids"][0],
                    result["embeddings"][0],
                    result["metadatas"][0],
                    result["documents"][0]
                )
            ]

            logger.debug(f"Found {len(forms)} similar forms")
            return forms

        except Exception as e:
            raise GLCSMemoryError(f"Failed to search similar forms: {str(e)} (top_k: {top_k})")

    def search_by_entity(self, entity_name: str, context_id: Optional[str] = None) -> List[LogicalForm]:
        """
        Search for LogicalForms mentioning a specific entity.

        Searches both subject and object fields.

        Args:
            entity_name: Entity name to search for (case-sensitive)

        Returns:
            List of LogicalForms mentioning the entity

        Example:
            >>> socrates_forms = manager.search_by_entity("socrates")
        """
        try:
            # Search for entity as subject or object
            # Note: ChromaDB doesn't support OR queries directly, so we do two queries

            # Search as subject
            where_subject = {"subject_name": entity_name}
            if context_id:
                where_subject = {"$and": [{"subject_name": entity_name}, {"context_id": context_id}]}
            result_subject = self.collection.get(
                where=where_subject,
                include=["embeddings", "metadatas", "documents"]
            )

            # Search as object
            where_object = {"object_name": entity_name}
            if context_id:
                where_object = {"$and": [{"object_name": entity_name}, {"context_id": context_id}]}
            result_object = self.collection.get(
                where=where_object,
                include=["embeddings", "metadatas", "documents"]
            )

            # Combine results (deduplicate by form_id)
            seen_ids = set()
            forms = []

            for result in [result_subject, result_object]:
                for form_id, embedding, metadata, document in zip(
                    result["ids"],
                    result["embeddings"],
                    result["metadatas"],
                    result["documents"]
                ):
                    if form_id not in seen_ids:
                        seen_ids.add(form_id)
                        forms.append(self._reconstruct_form(
                            form_id=UUID(form_id),
                            embedding=np.array(embedding),
                            metadata=metadata,
                            source_text=document
                        ))

            logger.debug(f"Found {len(forms)} forms mentioning entity '{entity_name}'")
            return forms

        except Exception as e:
            raise GLCSMemoryError(f"Failed to search by entity: {str(e)} (entity_name: {entity_name})")

    def search_by_relation(self, verb: str) -> List[LogicalForm]:
        """
        Search for LogicalForms with a specific relation/predicate.

        Args:
            verb: Predicate verb to search for (case-sensitive)

        Returns:
            List of LogicalForms with the specified predicate

        Example:
            >>> is_forms = manager.search_by_relation("is")
        """
        try:
            result = self.collection.get(
                where={"predicate_verb": verb},
                include=["embeddings", "metadatas", "documents"]
            )

            forms = [
                self._reconstruct_form(
                    form_id=UUID(form_id),
                    embedding=np.array(embedding),
                    metadata=metadata,
                    source_text=document
                )
                for form_id, embedding, metadata, document in zip(
                    result["ids"],
                    result["embeddings"],
                    result["metadatas"],
                    result["documents"]
                )
            ]

            logger.debug(f"Found {len(forms)} forms with relation '{verb}'")
            return forms

        except Exception as e:
            raise GLCSMemoryError(f"Failed to search by relation: {str(e)} (verb: {verb})")

    # ========================================================================
    # CONTEXT MANAGEMENT
    # ========================================================================

    def list_contexts(self) -> List[str]:
        """
        List all unique context IDs in the database.

        Returns:
            List of context ID strings

        Example:
            >>> contexts = manager.list_contexts()
            >>> print(f"Found {len(contexts)} contexts: {contexts}")
        """
        try:
            # Paginate through metadata to avoid a single huge allocation (#35).
            # At most _PAGE_SIZE records are in memory at any point.
            _PAGE_SIZE = 1000
            contexts: set = set()
            offset = 0
            while True:
                result = self.collection.get(
                    include=["metadatas"],
                    limit=_PAGE_SIZE,
                    offset=offset,
                )
                batch = result.get("metadatas") or []
                for metadata in batch:
                    contexts.add(metadata["context_id"])
                if len(batch) < _PAGE_SIZE:
                    break
                offset += _PAGE_SIZE

            context_list = sorted(contexts)
            logger.debug(f"Found {len(context_list)} contexts")
            return context_list

        except Exception as e:
            raise GLCSMemoryError(f"Failed to list contexts: {str(e)}")

    def clear_context(self, context_id: str) -> int:
        """
        Delete all LogicalForms in a specific context.

        Args:
            context_id: Context/session ID to clear

        Returns:
            Number of forms deleted

        Example:
            >>> deleted = manager.clear_context("session_123")
            >>> print(f"Deleted {deleted} forms")
        """
        try:
            # Get all form IDs in the context
            result = self.collection.get(
                where={"context_id": context_id},
                include=[]  # Only need IDs
            )

            form_ids = result["ids"]
            count = len(form_ids)

            if count > 0:
                self.collection.delete(ids=form_ids)
                logger.info(f"Cleared {count} forms from context '{context_id}'")

            return count

        except Exception as e:
            raise GLCSMemoryError(f"Failed to clear context: {str(e)} (context_id: {context_id})")

    def clear_all(self) -> int:
        """
        Delete all LogicalForms from all contexts in the store.

        Returns:
            Total number of forms deleted

        Example:
            >>> deleted = manager.clear_all()
            >>> print(f"Wiped {deleted} forms from database")
        """
        try:
            count = self.collection.count()
            if count > 0:
                # Get all IDs
                result = self.collection.get(include=[])
                self.collection.delete(ids=result["ids"])
                logger.info(f"Cleared all {count} forms from memory store")
            return count

        except Exception as e:
            raise GLCSMemoryError(f"Failed to clear all forms: {str(e)}")

    def get_context_stats(self, context_id: str) -> Dict:
        """
        Get statistics about a specific context.

        Args:
            context_id: Context/session ID

        Returns:
            Dict with statistics:
                - total_forms: Number of forms
                - logical_types: Count by logical type
                - polarities: Count by polarity
                - avg_confidence: Average confidence score

        Example:
            >>> stats = manager.get_context_stats("session_123")
            >>> print(f"Total forms: {stats['total_forms']}")
            >>> print(f"Average confidence: {stats['avg_confidence']:.2f}")
        """
        try:
            # Query metadata only — no embeddings or documents needed (#36).
            # This avoids reconstructing full LogicalForm objects with numpy arrays.
            result = self.collection.get(
                where={"context_id": context_id},
                include=["metadatas"],
            )
            metadatas = result.get("metadatas") or []

            if not metadatas:
                return {
                    "total_forms": 0,
                    "logical_types": {},
                    "polarities": {},
                    "avg_confidence": 0.0,
                }

            logical_types: dict = {}
            polarities: dict = {}
            total_confidence = 0.0

            for meta in metadatas:
                lt = meta["logical_type"]
                logical_types[lt] = logical_types.get(lt, 0) + 1

                pol = meta["polarity"]
                polarities[pol] = polarities.get(pol, 0) + 1

                total_confidence += meta.get("confidence_score", 0.0)

            stats = {
                "total_forms": len(metadatas),
                "logical_types": logical_types,
                "polarities": polarities,
                "avg_confidence": total_confidence / len(metadatas),
            }

            logger.debug(f"Generated stats for context '{context_id}': {stats}")
            return stats

        except Exception as e:
            raise GLCSMemoryError(f"Failed to get context stats: {str(e)} (context_id: {context_id})")

    def count_all_forms(self) -> int:
        """
        Get total number of forms in the database.

        Returns:
            Total count of stored forms

        Example:
            >>> total = manager.count_all_forms()
            >>> print(f"Database contains {total} forms")
        """
        return self.collection.count()

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _build_metadata(self, form: LogicalForm) -> Dict:
        """Build a ChromaDB-compatible metadata dict from a LogicalForm.

        Scalar fields (context_id, logical_type, etc.) are stored for fast
        WHERE-clause filtering.  The full form is also stored as a JSON string
        so that _reconstruct_form can do a lossless round-trip (#41, #42).
        """
        return {
            "context_id": form.context_id,
            "logical_type": form.logical_type.value,
            "polarity": form.polarity.value,
            "subject_name": form.subject.name,
            "subject_entity_type": form.subject.entity_type or "",
            "predicate_verb": form.predicate.verb,
            "object_name": form.object.name if form.object else "",
            "object_entity_type": (form.object.entity_type or "") if form.object else "",
            "confidence_score": form.confidence_score,
            "timestamp": form.timestamp.isoformat(),
            # Full serialisation (embedding excluded — stored as the native vector).
            "form_json": form.model_dump_json(exclude={"embedding"}),
        }

    def _reconstruct_form(
        self,
        form_id: UUID,
        embedding: np.ndarray,
        metadata: Dict,
        source_text: str
    ) -> LogicalForm:
        """Reconstruct a LogicalForm from ChromaDB storage.

        When form_json is present (all forms stored after #41 was fixed) the
        reconstruction is lossless — entity IDs, relation IDs, relation_type,
        and all metadata dicts are restored exactly.  For legacy records written
        before that fix a best-effort reconstruction from the scalar metadata
        fields is used as a fallback.
        """
        if "form_json" in metadata:
            form = LogicalForm.model_validate_json(metadata["form_json"])
            form.form_id = form_id  # use ChromaDB's authoritative ID
            form.embedding = embedding
            return form

        # Legacy fallback: reconstruct from scalar metadata fields only.
        from datetime import datetime
        from glcs.core.models import Entity, Relation, LogicalType, Polarity

        subject = Entity(
            name=metadata["subject_name"],
            entity_type=metadata.get("subject_entity_type") or None
        )
        predicate = Relation(verb=metadata["predicate_verb"])
        obj = (
            Entity(
                name=metadata["object_name"],
                entity_type=metadata.get("object_entity_type") or None
            )
            if metadata["object_name"] else None
        )
        form = LogicalForm(
            context_id=metadata["context_id"],
            logical_type=LogicalType(metadata["logical_type"]),
            subject=subject,
            predicate=predicate,
            object=obj,
            polarity=Polarity(metadata["polarity"]),
            source_text=source_text,
            confidence_score=metadata["confidence_score"]
        )
        form.form_id = form_id
        form.timestamp = datetime.fromisoformat(metadata["timestamp"])
        form.embedding = embedding
        return form
