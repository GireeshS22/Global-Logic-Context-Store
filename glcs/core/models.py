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

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    timestamp: datetime = Field(default_factory=datetime.utcnow)
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

    @field_validator('embedding')
    @classmethod
    def validate_embedding_dimension(cls, v: Optional[np.ndarray]) -> Optional[np.ndarray]:
        """Validate that embedding is 768-dimensional if present."""
        if v is not None:
            if not isinstance(v, np.ndarray):
                raise ValueError("Embedding must be a numpy array")
            if v.shape != (768,):
                raise ValueError(f"Embedding must be 768-dimensional, got shape {v.shape}")
        return v

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """
        Override to convert numpy array to list for JSON serialization.
        """
        data = super().model_dump(**kwargs)
        if data.get('embedding') is not None:
            data['embedding'] = data['embedding'].tolist()
        return data


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
        ...     violation_type="CONTRADICTION",
        ...     conflicting_forms=[form1_id, form2_id],
        ...     severity="HIGH",
        ...     explanation="Universal rule contradicts ground fact"
        ... )
    """

    violation_id: UUID = Field(default_factory=uuid4)
    violation_type: str = Field(..., min_length=1)
    conflicting_forms: List[UUID] = Field(..., min_length=2)
    severity: str = Field(..., pattern="^(HIGH|MEDIUM|LOW)$")
    explanation: str = Field(..., min_length=1)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
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
    is_consistent: bool
    violations: List[Violation] = Field(default_factory=list)
    total_forms_checked: int = Field(..., ge=0)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_consistency(self) -> 'ConsistencyReport':
        """
        Validate that is_consistent matches the violations list.

        is_consistent must be True if violations is empty, False otherwise.
        """
        expected_consistent = len(self.violations) == 0
        if self.is_consistent != expected_consistent:
            raise ValueError(
                f"is_consistent={self.is_consistent} but violations list has "
                f"{len(self.violations)} items. These must match."
            )
        return self
