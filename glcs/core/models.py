"""
Core data models for GLCS (Global Logical Context Store).

This module defines Pydantic data models (schemas) that represent the core
data structures used throughout the GLCS system. These are NOT machine learning
models, but rather data validation and serialization classes.

Models:
    - Entity: Represents subjects and objects in logical statements
    - Relation: Represents predicates/verbs connecting entities
    - LogicalType: Enum for categorizing logical statement types
    - Polarity: Enum for affirmative vs negative statements
    - LogicalForm: Core structure for parsed logical statements
    - Violation: Represents detected logical inconsistencies
    - ConsistencyReport: API response format for consistency checks

All models use Pydantic v2 for automatic validation, type checking, and
JSON serialization.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_serializer, field_validator


# ============================================================================
# ENUMS
# ============================================================================


class LogicalType(str, Enum):
    """
    Categorizes logical statements by their logical structure.

    Different logical types have different consistency rules and priorities.
    """

    UNIVERSAL_RULE = "universal_rule"
    """
    Universal quantification: ∀x: P(x) → Q(x)
    Example: "All humans are mortal"
    Priority: Highest (strongest claims)
    """

    EXISTENTIAL_CLAIM = "existential_claim"
    """
    Existential quantification: ∃x: P(x)
    Example: "There exists a human named Socrates"
    Priority: Low
    """

    CONDITIONAL_LOGIC = "conditional_logic"
    """
    If-then statements: P → Q
    Example: "If it rains, then the ground is wet"
    Priority: Medium
    """

    GROUND_FACT = "ground_fact"
    """
    Simple assertions: P(a)
    Example: "Socrates is human"
    Priority: Context-specific (can contradict universals)
    """


class Polarity(str, Enum):
    """
    Indicates whether a statement is affirmative or negative.

    Critical for contradiction detection.
    """

    POSITIVE = "positive"
    """Affirmative statement: "X is Y" """

    NEGATIVE = "negative"
    """Negative statement: "X is not Y" """


class ViolationType(str, Enum):
    """
    Typed enumeration of all violation categories produced by ConsistencyChecker.

    Using an enum (instead of a free-form string) gives IDE autocomplete, prevents
    typos, and makes exhaustive matching possible.
    """

    POLARITY_CONTRADICTION = "POLARITY_CONTRADICTION"
    UNIVERSAL_GROUND_CONTRADICTION = "UNIVERSAL_GROUND_CONTRADICTION"
    EXACT_REDUNDANCY = "EXACT_REDUNDANCY"
    SEMANTIC_REDUNDANCY = "SEMANTIC_REDUNDANCY"


class Severity(str, Enum):
    """Severity level for a detected Violation."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ============================================================================
# ENTITY AND RELATION MODELS
# ============================================================================


class Entity(BaseModel):
    """
    Represents a subject or object in a logical statement.

    Entities are the "nouns" in logical forms. They can represent people,
    concepts, objects, or any named thing that participates in a relation.

    Attributes:
        entity_id: Unique identifier (auto-generated)
        name: String name of the entity
        entity_type: Optional category (e.g., "person", "concept", "object")
        metadata: Optional additional properties

    Example:
        >>> entity = Entity(name="Socrates", entity_type="person")
        >>> entity.name
        'socrates'  # Normalized to lowercase
    """

    entity_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    entity_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('name')
    @classmethod
    def normalize_name(cls, v: str) -> str:
        """Normalize entity name to lowercase and trim whitespace."""
        return v.strip().lower()


class Relation(BaseModel):
    """
    Represents a predicate/verb connecting entities.

    Relations are the "verbs" in logical forms. They describe the relationship
    between entities.

    Attributes:
        relation_id: Unique identifier (auto-generated)
        verb: String predicate/verb
        relation_type: Optional category (e.g., "property", "location", "action")
        metadata: Optional additional properties

    Example:
        >>> relation = Relation(verb="is_mortal", relation_type="property")
        >>> relation.verb
        'is_mortal'
    """

    relation_id: UUID = Field(default_factory=uuid4)
    verb: str = Field(..., min_length=1)
    relation_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('verb')
    @classmethod
    def normalize_verb(cls, v: str) -> str:
        """Normalize verb to lowercase and trim whitespace."""
        return v.strip().lower()


# ============================================================================
# LOGICAL FORM MODEL (CRITICAL)
# ============================================================================


class LogicalForm(BaseModel):
    """
    Core data structure representing a parsed logical statement.

    This is the normalized representation that ALL GLCS components work with:
    - Logical Parser produces LogicalForm objects
    - Semantic Encoder adds embeddings to LogicalForm
    - Memory Manager stores LogicalForm objects
    - Consistency Checker compares LogicalForm objects

    Attributes:
        form_id: Unique identifier (auto-generated)
        context_id: Session/conversation identifier (groups related statements)
        timestamp: When the statement was created (auto-generated)
        logical_type: Type of logical statement (UNIVERSAL_RULE, etc.)
        subject: Entity representing the subject
        predicate: Relation representing the verb/predicate
        object: Optional entity representing the object (for binary relations)
        polarity: POSITIVE or NEGATIVE
        confidence_score: Parser confidence (0.0-1.0, default 1.0)
        source_text: Original natural language input
        embedding: Optional 768-dimensional semantic vector
        metadata: Optional additional properties

    Example:
        >>> form = LogicalForm(
        ...     context_id="session_123",
        ...     logical_type=LogicalType.UNIVERSAL_RULE,
        ...     subject=Entity(name="humans"),
        ...     predicate=Relation(verb="are"),
        ...     object=Entity(name="mortal"),
        ...     polarity=Polarity.POSITIVE,
        ...     source_text="All humans are mortal"
        ... )
    """

    form_id: UUID = Field(default_factory=uuid4)
    context_id: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    logical_type: LogicalType
    subject: Entity
    predicate: Relation
    object: Optional[Entity] = None
    polarity: Polarity
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    source_text: str = Field(..., min_length=1)
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Allow numpy arrays
        validate_assignment=True  # Run validators on field assignment
    )

    def __repr__(self) -> str:
        """Custom repr to hide massive embedding array in logs."""
        emb_str = f"np.ndarray(shape={self.embedding.shape})" if self.embedding is not None else "None"
        return (
            f"LogicalForm(form_id={self.form_id}, context_id='{self.context_id}', "
            f"type={self.logical_type.value}, subject='{self.subject.name}', "
            f"predicate='{self.predicate.verb}', object='{self.object.name if self.object else None}', "
            f"polarity={self.polarity.value}, embedding={emb_str})"
        )

    def __str__(self) -> str:
        """Friendly string representation."""
        return f"[{self.logical_type.value.upper()}] {self.source_text} ({self.polarity.value})"

    @field_validator('embedding', mode='before')
    @classmethod
    def coerce_and_validate_embedding(cls, v: Any) -> Optional[np.ndarray]:
        """Accept list or numpy array; validate it is a non-empty 1D array.

        (#14) Accepting a list means LogicalForm(**form.model_dump()) round-trips
        correctly — model_dump() serializes to list, this validator converts it back.
        (#37) Dimension is intentionally not hard-coded here — the SemanticEncoder
        is responsible for ensuring correct dimensions when generating embeddings.
        """
        if v is None:
            return v
        if isinstance(v, list):
            v = np.array(v, dtype=np.float64)
        if not isinstance(v, np.ndarray):
            raise ValueError("Embedding must be a numpy array or list")
        if v.ndim != 1 or len(v) == 0:
            raise ValueError(f"Embedding must be a non-empty 1D array, got shape {v.shape}")
        return v

    @field_serializer('embedding')
    def serialize_embedding(self, v: Optional[np.ndarray]) -> Optional[list]:
        """Convert numpy array to list for all serialization paths.

        (#15) Called by both model_dump() and model_dump_json(), so numpy arrays
        are never passed raw to json.dumps().
        """
        return v.tolist() if v is not None else None


# ============================================================================
# VIOLATION AND REPORT MODELS
# ============================================================================


class Violation(BaseModel):
    """
    Represents a detected logical inconsistency.

    Created by the Consistency Checker when logical conflicts are found.

    Attributes:
        violation_id: Unique identifier (auto-generated)
        violation_type: Category of violation (e.g., "CONTRADICTION")
        conflicting_forms: List of LogicalForm IDs that conflict (minimum 2)
        severity: HIGH, MEDIUM, or LOW
        explanation: Human-readable description of the violation
        detected_at: Timestamp when violation was detected (auto-generated)
        metadata: Optional additional properties

    Example:
        >>> violation = Violation(
        ...     violation_type=ViolationType.UNIVERSAL_GROUND_CONTRADICTION,
        ...     conflicting_forms=[form1_id, form2_id],
        ...     severity=Severity.HIGH,
        ...     explanation="Universal rule contradicts ground fact"
        ... )
    """

    violation_id: UUID = Field(default_factory=uuid4)
    violation_type: ViolationType
    conflicting_forms: List[UUID] = Field(..., min_length=2)
    severity: Severity
    explanation: str = Field(..., min_length=1)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConsistencyReport(BaseModel):
    """
    API response format for consistency checking.

    This is the final output returned to API users after checking a context
    for logical consistency.

    Attributes:
        report_id: Unique identifier (auto-generated)
        context_id: Session/conversation that was checked
        is_consistent: True if no violations found, False otherwise
        violations: List of detected violations (empty if consistent)
        total_forms_checked: Number of logical forms analyzed
        generated_at: Timestamp when report was generated (auto-generated)
        metadata: Optional additional properties

    Example:
        >>> report = ConsistencyReport(
        ...     context_id="session_123",
        ...     is_consistent=False,
        ...     violations=[violation1, violation2],
        ...     total_forms_checked=15
        ... )
    """

    report_id: UUID = Field(default_factory=uuid4)
    context_id: str = Field(..., min_length=1)
    violations: List[Violation] = Field(default_factory=list)
    total_forms_checked: int = Field(..., ge=0)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def is_consistent(self) -> bool:
        """True iff no violations were detected. Auto-derived — never pass manually."""
        return len(self.violations) == 0


class BatchResult(BaseModel):
    """
    Generic container for batch operation results (#72, #73).
    
    Tracks successful items and failures separately to ensure transparency.
    
    Attributes:
        successes: List of successfully processed items
        errors: List of dicts with 'index', 'text', and 'error' keys
        total_count: Total number of items in the batch
    """
    successes: List[Any] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    total_count: int = 0

    @computed_field
    @property
    def success_count(self) -> int:
        return len(self.successes)

    @computed_field
    @property
    def error_count(self) -> int:
        return len(self.errors)

    @computed_field
    @property
    def all_successful(self) -> bool:
        return len(self.errors) == 0
