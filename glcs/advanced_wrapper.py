"""
Advanced GLCS Wrapper - PhD Research Implementation

This module provides the main interface for the advanced GLCS system,
integrating all PhD research components:
- LLM-based logical parser
- Semantic encoder (768-dim embeddings)
- Vector-based memory manager (ChromaDB)
- Advanced consistency checker

This is the research-grade implementation for detecting logical inconsistencies
in LLM conversations using neuro-symbolic methods.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from glcs.core import (
    LLMLogicalParser,
    SemanticEncoder,
    MemoryManager,
    ConsistencyChecker,
    LogicalForm,
    ConsistencyReport,
)
from glcs.utils.logger import get_logger
from glcs.utils.exceptions import ParsingError, GLCSMemoryError, ConsistencyError

logger = get_logger(__name__)


class AdvancedGLCS:
    """
    Advanced GLCS System - PhD Research Implementation

    This class provides a high-level interface to the complete GLCS research
    system. It integrates:

    1. LLM-based parsing (extracts structured LogicalForm from natural language)
    2. Semantic encoding (generates 768-dimensional embeddings)
    3. Vector memory storage (stores in ChromaDB with similarity search)
    4. Advanced consistency checking (detects contradictions using semantics)

    Workflow:
        Input → LLM Parser → LogicalForm → Semantic Encoder → Add Embeddings
          → Consistency Checker → If consistent → Memory Manager → Store
          → Return ConsistencyReport

    Example:
        >>> glcs = AdvancedGLCS(parser_provider='ollama')
        >>>
        >>> # Store facts
        >>> result = glcs.process_statement("All employees work remotely", "ctx-123")
        >>> print(result.is_consistent)  # True
        >>>
        >>> # Detect contradiction
        >>> result = glcs.process_statement("John works from office", "ctx-123")
        >>> if not result.is_consistent:
        ...     print(result.violations[0].explanation)
    """

    def __init__(
        self,
        parser_provider: str = 'ollama',
        parser_model: Optional[str] = None,
        encoder_model: str = 'all-mpnet-base-v2',
        memory_path: Optional[str] = None,
        collection_name: str = 'glcs_advanced',
        in_memory: bool = False,
        cache_parsing: bool = True,
    ):
        """
        Initialize the Advanced GLCS system.

        Args:
            parser_provider: LLM provider for parsing ('ollama', 'openai', etc.)
                           Default: 'ollama' (free, local, offline)
            parser_model: Model name for parser (optional, uses provider default)
            encoder_model: Sentence transformer model for embeddings
                          Default: 'all-mpnet-base-v2' (768-dim)
            memory_path: Path for ChromaDB persistence (None = temp directory)
            collection_name: ChromaDB collection name
            in_memory: If True, use in-memory ChromaDB (for testing)
            cache_parsing: Enable caching of parse results
        """
        logger.info("Initializing Advanced GLCS system...")

        # Initialize LLM Parser
        logger.info(f"Initializing LLM parser with provider: {parser_provider}")
        self.parser = LLMLogicalParser(
            provider=parser_provider,
            model=parser_model,
            cache_enabled=cache_parsing,
        )

        # Initialize Semantic Encoder
        logger.info(f"Initializing semantic encoder: {encoder_model}")
        self.encoder = SemanticEncoder(model_name=encoder_model)

        # Initialize Memory Manager
        logger.info(f"Initializing memory manager (collection: {collection_name})")
        self.memory = MemoryManager(
            collection_name=collection_name,
            persist_directory=memory_path,
            in_memory=in_memory,
        )

        # Initialize Consistency Checker
        logger.info("Initializing consistency checker")
        self.checker = ConsistencyChecker(
            self.memory,
            self.encoder,
        )

        logger.info("Advanced GLCS system initialized successfully")

    def process_statement(
        self,
        text: str,
        context_id: str,
        auto_store: bool = True,
    ) -> ConsistencyReport:
        """
        Process a natural language statement through the complete pipeline.

        This is the main method for using GLCS. It:
        1. Parses the statement using LLM
        2. Adds semantic embeddings
        3. Checks consistency against stored knowledge
        4. Optionally stores if consistent
        5. Returns detailed report

        Args:
            text: Natural language statement to process
            context_id: Context/session identifier
            auto_store: If True, automatically store consistent statements

        Returns:
            ConsistencyReport with results and any violations

        Raises:
            ParsingError: If statement cannot be parsed

        Example:
            >>> glcs = AdvancedGLCS()
            >>> report = glcs.process_statement(
            ...     "All managers must approve budgets",
            ...     context_id="meeting-2024"
            ... )
            >>> if report.is_consistent:
            ...     print(f"Stored successfully")
            >>> else:
            ...     for violation in report.violations:
            ...         print(f"⚠️ {violation.explanation}")
        """
        logger.info(f"Processing statement: {text[:50]}...")

        try:
            # Step 1: Parse using LLM
            logger.debug("Step 1: Parsing with LLM")
            form = self.parser.parse(text, context_id)
            logger.info(f"Parsed as {form.logical_type.value} (confidence: {form.confidence_score:.2f})")

            # Step 2: Add semantic embeddings
            logger.debug("Step 2: Adding embeddings")
            self.encoder.add_embedding_to_form(form)
            logger.debug(f"Added {form.embedding.shape[0]}-dim embedding")

            # Step 3: Check consistency
            logger.debug("Step 3: Checking consistency")
            report = self.checker.check_form_against_context(form, context_id)

            # Step 4: Store if consistent and auto_store enabled
            if report.is_consistent and auto_store:
                logger.debug("Step 4: Storing in memory")
                form_id = self.memory.store_form(form)
                logger.info(f"Stored successfully (ID: {form_id})")
            elif not report.is_consistent:
                logger.warning(f"Statement inconsistent: {len(report.violations)} violations")

            return report

        except ParsingError as e:
            logger.error(f"Parsing failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise

    def process_batch(
        self,
        texts: List[str],
        context_id: str,
        auto_store: bool = True,
    ) -> "BatchResult":
        """
        Process multiple statements efficiently.

        Args:
            texts: List of natural language statements
            context_id: Context identifier for all statements
            auto_store: If True, store consistent statements

        Returns:
            BatchResult containing reports for successful items and error details (#73)
        """
        # (#73: Full transparency — track successes and errors separately)
        from glcs.core.models import BatchResult
        
        logger.info(f"Processing batch of {len(texts)} statements")
        successes = []
        errors = []

        for i, text in enumerate(texts):
            logger.debug(f"Processing item {i+1}/{len(texts)}")
            try:
                report = self.process_statement(text, context_id, auto_store)
                successes.append(report)
            except Exception as e:
                logger.warning(f"Failed to process statement {i} ('{text[:30]}...'): {e}")
                errors.append({
                    'index': i,
                    'text': text,
                    'error': str(e)
                })

        logger.info(f"Batch processing complete: {len(successes)}/{len(texts)} successful")
        
        return BatchResult(
            successes=successes,
            errors=errors,
            total_count=len(texts)
        )

    def verify_context(self, context_id: str) -> ConsistencyReport:
        """
        Verify internal consistency of all statements in a context.

        This checks if the existing knowledge base has any internal
        contradictions, even if statements were added individually
        without conflicts.

        Args:
            context_id: Context to verify

        Returns:
            ConsistencyReport with any detected inconsistencies

        Example:
            >>> glcs = AdvancedGLCS()
            >>> # Add statements over time
            >>> glcs.process_statement("All birds can fly", "ctx-1")
            >>> glcs.process_statement("Penguins are birds", "ctx-1")
            >>> glcs.process_statement("Penguins cannot fly", "ctx-1")
            >>> # Later, verify entire context
            >>> report = glcs.verify_context("ctx-1")
            >>> if not report.is_consistent:
            ...     print("Found inconsistencies in knowledge base")
        """
        logger.info(f"Verifying context: {context_id}")
        report = self.checker.check_context_consistency(context_id)

        if report.is_consistent:
            logger.info(f"Context is consistent ({report.total_forms_checked} forms)")
        else:
            logger.warning(f"Context has {len(report.violations)} inconsistencies")

        return report

    def get_context_summary(self, context_id: str) -> Dict[str, Any]:
        """
        Get summary of all knowledge in a context.

        Args:
            context_id: Context to summarize

        Returns:
            Dictionary with statistics and samples
        """
        stats = self.memory.get_context_stats(context_id)
        forms = self.memory.get_forms_by_context(context_id)

        return {
            'context_id': context_id,
            'statistics': stats,
            'total_forms': len(forms),
            'sample_statements': [f.source_text for f in forms[:10]],
        }

    def search_similar(
        self,
        query: str,
        context_id: Optional[str] = None,
        top_k: int = 5,
    ) -> List[LogicalForm]:
        """
        Search for statements semantically similar to query.

        This uses the 768-dim embeddings to find statements with
        similar meaning, even if they use different words.

        Args:
            query: Query text
            context_id: Optional context filter
            top_k: Number of results to return

        Returns:
            List of similar LogicalForm objects

        Example:
            >>> glcs = AdvancedGLCS()
            >>> # Find statements similar to a query
            >>> similar = glcs.search_similar(
            ...     "Who are the managers?",
            ...     context_id="company-db",
            ...     top_k=5
            ... )
            >>> for form in similar:
            ...     print(f"- {form.source_text}")
        """
        logger.info(f"Searching for: {query[:50]}...")

        # Encode query
        query_embedding = self.encoder.encode(query)

        # Search in memory
        results = self.memory.search_similar_forms(
            query_embedding,
            top_k=top_k,
            context_id=context_id,
        )

        logger.info(f"Found {len(results)} similar statements")
        return results

    def get_forms_by_entity(
        self,
        entity_name: str,
        context_id: Optional[str] = None,
    ) -> List[LogicalForm]:
        """
        Get all statements mentioning a specific entity.

        Args:
            entity_name: Entity to search for
            context_id: Optional context filter

        Returns:
            List of LogicalForm objects mentioning the entity
        """
        logger.info(f"Searching for entity: {entity_name}")
        results = self.memory.search_by_entity(entity_name, context_id=context_id)
        logger.info(f"Found {len(results)} statements about {entity_name}")
        return results

    def clear_context(self, context_id: str) -> int:
        """
        Clear all statements in a context.

        Args:
            context_id: Context to clear

        Returns:
            Number of statements deleted
        """
        logger.info(f"Clearing context: {context_id}")
        count = self.memory.clear_context(context_id)
        logger.info(f"Deleted {count} statements")
        return count

    def clear_all(self) -> int:
        """
        Clear all statements from all contexts in the knowledge base.

        Returns:
            Total number of statements deleted

        Example:
            >>> glcs = AdvancedGLCS()
            >>> deleted = glcs.clear_all()
            >>> print(f"Knowledge base reset. {deleted} records removed.")
        """
        logger.info("Wiping entire knowledge base")
        count = self.memory.clear_all()
        logger.info(f"Deleted {count} statements in total")
        return count

    def save_state(self, file_path: str) -> int:
        """
        Save the entire knowledge base state to a portable JSON file.

        Args:
            file_path: Destination path for the state file

        Returns:
            Number of statements saved

        Example:
            >>> glcs.save_state("glcs_backup.json")
        """
        logger.info(f"Saving knowledge base state to: {file_path}")
        count = self.memory.save_state(file_path)
        logger.info(f"Successfully saved {count} statements")
        return count

    def load_state(self, file_path: str, clear_existing: bool = True) -> int:
        """
        Load knowledge base state from a portable JSON file.

        Args:
            file_path: Source path of the state file
            clear_existing: If True, wipes current memory before loading

        Returns:
            Number of statements loaded

        Example:
            >>> glcs.load_state("glcs_backup.json")
        """
        logger.info(f"Loading knowledge base state from: {file_path}")
        count = self.memory.load_state(file_path, clear_existing=clear_existing)
        logger.info(f"Successfully loaded {count} statements")
        return count

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get information about the GLCS system configuration.

        Returns:
            Dictionary with system information
        """
        return {
            'parser': {
                'provider': self.parser.provider_name,
                'cache_enabled': self.parser.cache_enabled,
                'cache_size': len(self.parser.cache),
            },
            'encoder': {
                'model': self.encoder.model_name,
                'dimensions': self.encoder.embedding_dim,
            },
            'memory': {
                'collection': self.memory.collection_name,
                'total_forms': len(self.memory.collection.get()['ids']),
            },
            'checker': {
                'redundancy_threshold': self.checker.redundancy_threshold,
            },
        }

    def switch_parser_provider(
        self,
        provider_name: str,
        model: Optional[str] = None,
    ) -> None:
        """
        Switch the LLM parser to a different provider.

        Useful for comparing parsing quality or switching from
        local (Ollama) to cloud (OpenAI) for better accuracy.

        Args:
            provider_name: New provider name
            model: Optional model override

        Example:
            >>> glcs = AdvancedGLCS(parser_provider='ollama')
            >>> # Switch to GPT-4 for higher accuracy
            >>> glcs.switch_parser_provider('openai', model='gpt-4o')
        """
        logger.info(f"Switching parser to: {provider_name}")
        self.parser.switch_provider(provider_name, model=model)
        logger.info("Parser switched successfully")
