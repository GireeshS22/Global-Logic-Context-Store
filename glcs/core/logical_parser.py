"""
LLM-Based Logical Parser for Advanced Statement Processing.

This module provides an LLM-powered parser that extracts structured logical
representations from natural language text. Unlike regex-based parsing, this
parser uses large language models to understand complex sentence structures,
implicit meanings, and contextual nuances.

Key Features:
- Multi-provider support (OpenAI, Anthropic, Gemini, Groq, Ollama)
- Extracts rich LogicalForm objects with metadata
- Handles complex sentences that regex parsers cannot
- Automatic confidence scoring based on extraction quality
- Caching to reduce API costs and improve speed
- Retry logic with exponential backoff
- Batch processing for efficiency

Author: GLCS PhD Research Team
Version: 1.0.0 (Stage 1.5)
"""

import json
import time
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from uuid import uuid4

from glcs.core.models import (
    LogicalForm,
    Entity,
    Relation,
    LogicalType,
    Polarity,
)
from glcs.providers import LLMProvider, ProviderFactory, ProviderConfig, ProviderError
from glcs.utils.exceptions import ParsingError, ValidationError
from glcs.utils.logger import get_logger

logger = get_logger(__name__)


class LLMLogicalParser:
    """
    LLM-powered parser for extracting logical structures from natural language.

    This parser uses large language models to convert natural language statements
    into structured LogicalForm objects. It supports multiple LLM providers and
    includes sophisticated error handling, caching, and optimization features.

    The parser follows this workflow:
    1. Receive natural language text
    2. Send to LLM with structured extraction prompt
    3. Parse LLM response (JSON format)
    4. Validate and create LogicalForm object
    5. Calculate confidence score
    6. Cache result for future use

    Attributes:
        provider: LLM provider instance for parsing
        provider_name: Name of the current provider
        cache: In-memory cache for parsed results
        cache_enabled: Whether caching is enabled
        max_retries: Maximum retry attempts on failure
        timeout: Request timeout in seconds

    Example:
        >>> parser = LLMLogicalParser(provider='ollama', model='llama3.2')
        >>> form = parser.parse("All employees must complete training", "ctx-123")
        >>> print(form.logical_type)  # LogicalType.UNIVERSAL_RULE
        >>> print(form.subject.name)  # "employees"
        >>> print(form.confidence_score)  # 0.95
    """

    # System prompt template for LLM parsing
    SYSTEM_PROMPT = """You are a logical statement parser. Your task is to extract structured logical information from natural language statements.

Extract the following components:
1. **Subject**: The main entity (who/what the statement is about)
2. **Predicate**: The relation/verb connecting subject and object
3. **Object**: The target entity (optional, may be None for unary predicates)
4. **Logical Type**: One of:
   - "universal_rule": Universal quantification (All X are Y, Every X has Y, No X are Y)
   - "existential_claim": Existential quantification (There exists X, Some Y are Z)
   - "conditional_logic": If-then statements (If X then Y, When X, Y)
   - "ground_fact": Simple assertions (John is X, Mary has Y)
5. **Polarity**: "positive" or "negative"
6. **Confidence**: Your confidence in the extraction (0.0 to 1.0)

Output ONLY valid JSON with this exact structure:
{
  "subject": {"name": "entity_name", "type": "entity_type or null"},
  "predicate": {"verb": "action_or_property", "type": "relation_type or null"},
  "object": {"name": "entity_name", "type": "entity_type or null"} or null,
  "logical_type": "universal_rule|existential_claim|conditional_logic|ground_fact",
  "polarity": "positive|negative",
  "confidence": 0.95
}

Examples:

Input: "All employees must complete training"
Output: {"subject": {"name": "employees", "type": "person"}, "predicate": {"verb": "must_complete", "type": "requirement"}, "object": {"name": "training", "type": "activity"}, "logical_type": "universal_rule", "polarity": "positive", "confidence": 0.95}

Input: "John is a manager"
Output: {"subject": {"name": "john", "type": "person"}, "predicate": {"verb": "is", "type": "property"}, "object": {"name": "manager", "type": "role"}, "logical_type": "ground_fact", "polarity": "positive", "confidence": 0.98}

Input: "If the server crashes, it will restart automatically"
Output: {"subject": {"name": "server", "type": "system"}, "predicate": {"verb": "crashes_then_restarts", "type": "causation"}, "object": {"name": "restart", "type": "action"}, "logical_type": "conditional_logic", "polarity": "positive", "confidence": 0.92}

Input: "Alice is not an engineer"
Output: {"subject": {"name": "alice", "type": "person"}, "predicate": {"verb": "is", "type": "property"}, "object": {"name": "engineer", "type": "role"}, "logical_type": "ground_fact", "polarity": "negative", "confidence": 0.97}

Now extract from the following statement. Return ONLY the JSON, no additional text."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        cache_enabled: bool = True,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        """
        Initialize the LLM-based logical parser.

        Args:
            provider: Provider name ('ollama', 'openai', 'anthropic', 'gemini', 'groq')
                     Default: 'ollama' (free, local, offline)
            model: Model name (e.g., 'llama3.2', 'gpt-4o-mini', 'claude-3-haiku')
            api_key: API key for cloud providers (not needed for Ollama)
            config: Additional provider configuration
            cache_enabled: Enable in-memory caching of parsed results
            max_retries: Maximum retry attempts on parsing failure
            timeout: Request timeout in seconds

        Raises:
            ProviderError: If provider initialization fails
        """
        # Default to Ollama for offline/local usage
        self.provider_name = provider or 'ollama'
        self.cache_enabled = cache_enabled
        self.max_retries = max_retries
        self.timeout = timeout

        # Initialize cache
        self.cache: Dict[str, LogicalForm] = {}

        # Create provider configuration
        provider_config = {
            'model': model or self._get_default_model(self.provider_name),
            'temperature': 0.1,  # Low temperature for consistency
            'max_tokens': 300,
            'timeout': timeout,
        }

        if api_key:
            provider_config['api_key'] = api_key

        if config:
            provider_config.update(config)

        # Create provider instance
        try:
            config_obj = ProviderConfig(**provider_config)
            self.provider: LLMProvider = ProviderFactory.create(
                self.provider_name,
                config=config_obj
            )
            logger.info(f"LLMLogicalParser initialized with provider: {self.provider_name}")
        except Exception as e:
            logger.error(f"Failed to initialize provider {self.provider_name}: {e}")
            raise ProviderError(f"Parser initialization failed: {e}")

    def _get_default_model(self, provider_name: str) -> str:
        """Get default model for each provider (optimized for accuracy)."""
        defaults = {
            'ollama': 'llama3.2',
            'openai': 'gpt-4o-mini',
            'anthropic': 'claude-3-5-sonnet-20241022',
            'gemini': 'gemini-1.5-flash',
            'groq': 'llama-3.1-70b-versatile',
        }
        return defaults.get(provider_name, 'llama3.2')

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def parse(
        self,
        text: str,
        context_id: str,
        use_cache: bool = True,
    ) -> LogicalForm:
        """
        Parse a single natural language statement into a LogicalForm.

        This is the main parsing method. It sends the text to the LLM,
        extracts structured information, validates the output, and creates
        a LogicalForm object.

        Args:
            text: Natural language statement to parse
            context_id: Context/session identifier for the statement
            use_cache: Whether to use cached results if available

        Returns:
            LogicalForm object with extracted structure and metadata

        Raises:
            ParsingError: If parsing fails after all retries
            ValidationError: If LLM output is invalid

        Example:
            >>> parser = LLMLogicalParser(provider='ollama')
            >>> form = parser.parse(
            ...     "All birds can fly",
            ...     context_id="conversation-123"
            ... )
            >>> print(f"Type: {form.logical_type}")
            >>> print(f"Subject: {form.subject.name}")
            >>> print(f"Confidence: {form.confidence_score}")
        """
        if not text or not text.strip():
            raise ValidationError("Cannot parse empty text")

        text = text.strip()

        # Check cache
        if use_cache and self.cache_enabled:
            cache_key = self._get_cache_key(text)
            if cache_key in self.cache:
                logger.debug(f"Cache hit for: {text[:50]}...")
                cached_form = self.cache[cache_key]
                # Update context_id to current context
                cached_form.context_id = context_id
                return cached_form

        # Parse with retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Call LLM
                extracted_data = self._call_llm(text)

                # Validate extracted data
                self._validate_extraction(extracted_data)

                # Create LogicalForm
                form = self._create_logical_form(
                    extracted_data,
                    text,
                    context_id
                )

                # Cache result
                if self.cache_enabled:
                    cache_key = self._get_cache_key(text)
                    self.cache[cache_key] = form

                logger.info(f"Successfully parsed: {text[:50]}... (confidence: {form.confidence_score:.2f})")
                return form

            except Exception as e:
                last_error = e
                logger.warning(f"Parse attempt {attempt + 1}/{self.max_retries} failed: {e}")

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.debug(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)

        # All retries failed
        error_msg = f"Failed to parse after {self.max_retries} attempts: {last_error}"
        logger.error(error_msg)
        raise ParsingError(error_msg)

    def _call_llm(self, text: str) -> Dict[str, Any]:
        """
        Call LLM to extract logical structure from text.

        Args:
            text: Input text to parse

        Returns:
            Dictionary with extracted fields

        Raises:
            ParsingError: If LLM call fails or returns invalid JSON
        """
        # Prepare messages
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]

        try:
            # Call provider
            response_text = self.provider.generate(
                messages,
                temperature=0.1,
                max_tokens=300,
            )

            # DEBUG: Log raw LLM response for debugging
            logger.debug(f"Raw LLM response (first 500 chars): {response_text[:500]}")

            # Parse JSON response
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith('```'):
                # Extract JSON from code block
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])  # Remove first and last line

            logger.debug(f"Cleaned response for JSON parsing: {response_text[:500]}")

            extracted_data = json.loads(response_text)
            logger.debug(f"Parsed JSON keys: {list(extracted_data.keys())}")
            return extracted_data

        except json.JSONDecodeError as e:
            raise ParsingError(f"LLM returned invalid JSON: {e}\nResponse: {response_text[:200]}")
        except Exception as e:
            raise ParsingError(f"LLM call failed: {e}")

    def _validate_extraction(self, data: Dict[str, Any]) -> None:
        """
        Validate extracted data structure and values.

        Args:
            data: Extracted data dictionary from LLM

        Raises:
            ValidationError: If data is invalid or incomplete
        """
        # Required fields
        required_fields = ['subject', 'predicate', 'logical_type', 'polarity', 'confidence']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        # Validate logical_type
        valid_types = ['universal_rule', 'existential_claim', 'conditional_logic', 'ground_fact']
        if data['logical_type'] not in valid_types:
            raise ValidationError(f"Invalid logical_type: {data['logical_type']}")

        # Validate polarity
        valid_polarities = ['positive', 'negative']
        if data['polarity'] not in valid_polarities:
            raise ValidationError(f"Invalid polarity: {data['polarity']}")

        # Validate confidence
        confidence = data['confidence']
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            raise ValidationError(f"Invalid confidence: {confidence} (must be 0.0-1.0)")

        # Validate subject
        if not isinstance(data['subject'], dict) or 'name' not in data['subject']:
            raise ValidationError("Invalid subject structure")

        # Validate predicate
        if not isinstance(data['predicate'], dict) or 'verb' not in data['predicate']:
            raise ValidationError("Invalid predicate structure")

        # Validate object (optional, but if present must have correct structure)
        if data.get('object') is not None:
            if not isinstance(data['object'], dict) or 'name' not in data['object']:
                raise ValidationError("Invalid object structure")

    def _create_logical_form(
        self,
        data: Dict[str, Any],
        source_text: str,
        context_id: str,
    ) -> LogicalForm:
        """
        Create LogicalForm object from extracted data.

        Args:
            data: Validated extraction data
            source_text: Original input text
            context_id: Context identifier

        Returns:
            LogicalForm object
        """
        # Create subject entity
        subject = Entity(
            name=data['subject']['name'].lower(),
            entity_type=data['subject'].get('type'),
        )

        # Create predicate relation
        predicate = Relation(
            verb=data['predicate']['verb'].lower(),
            relation_type=data['predicate'].get('type'),
        )

        # Create object entity (if present)
        obj = None
        if data.get('object') is not None:
            obj = Entity(
                name=data['object']['name'].lower(),
                entity_type=data['object'].get('type'),
            )

        # Create logical form
        form = LogicalForm(
            context_id=context_id,
            logical_type=LogicalType(data['logical_type']),
            subject=subject,
            predicate=predicate,
            object=obj,
            polarity=Polarity(data['polarity']),
            confidence_score=float(data['confidence']),
            source_text=source_text,
            timestamp=datetime.utcnow(),
        )

        return form

    def parse_batch(
        self,
        texts: List[str],
        context_id: str,
        use_cache: bool = True,
    ) -> List[LogicalForm]:
        """
        Parse multiple statements efficiently.

        For now, this processes statements sequentially. Future optimization
        could batch multiple statements into a single LLM call.

        Args:
            texts: List of natural language statements
            context_id: Context identifier for all statements
            use_cache: Whether to use cached results

        Returns:
            List of LogicalForm objects

        Example:
            >>> parser = LLMLogicalParser(provider='ollama')
            >>> texts = [
            ...     "All employees work remotely",
            ...     "John is an employee",
            ...     "Alice is a manager"
            ... ]
            >>> forms = parser.parse_batch(texts, "ctx-123")
            >>> print(f"Parsed {len(forms)} statements")
        """
        forms = []
        for text in texts:
            try:
                form = self.parse(text, context_id, use_cache=use_cache)
                forms.append(form)
            except Exception as e:
                logger.warning(f"Failed to parse '{text[:50]}...': {e}")
                # Continue with other statements
                continue

        logger.info(f"Batch parse: {len(forms)}/{len(texts)} successful")
        return forms

    def clear_cache(self) -> int:
        """
        Clear the parsing cache.

        Returns:
            Number of cached entries cleared
        """
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared {count} cached parse results")
        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            'enabled': self.cache_enabled,
            'size': len(self.cache),
            'provider': self.provider_name,
        }

    def switch_provider(
        self,
        provider_name: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Switch to a different LLM provider.

        This is useful for comparing parsing quality across providers
        or for failover scenarios.

        Args:
            provider_name: New provider name
            model: Optional model override
            api_key: Optional API key for new provider

        Example:
            >>> parser = LLMLogicalParser(provider='ollama')
            >>> # Try with GPT-4 for better accuracy
            >>> parser.switch_provider('openai', model='gpt-4o')
        """
        self.provider_name = provider_name

        provider_config = {
            'model': model or self._get_default_model(provider_name),
            'temperature': 0.1,
            'max_tokens': 300,
            'timeout': self.timeout,
        }

        if api_key:
            provider_config['api_key'] = api_key

        config_obj = ProviderConfig(**provider_config)
        self.provider = ProviderFactory.create(provider_name, config=config_obj)

        # Clear cache when switching providers
        self.clear_cache()

        logger.info(f"Switched to provider: {provider_name}")
