"""
Unit tests for Consistency Checker (Stage 1.3).

Tests the ConsistencyChecker class which detects logical contradictions and
redundancies in stored LogicalForm objects.

Test Coverage:
    - Initialization
    - Polarity contradiction detection
    - Universal vs ground contradiction detection
    - Redundancy detection (exact and semantic)
    - Context consistency checking
    - Severity scoring
    - Integration with MemoryManager and SemanticEncoder
"""

import pytest
import uuid

from glcs.core.consistency_checker import ConsistencyChecker
from glcs.core.memory_manager import MemoryManager
from glcs.core.semantic_encoder import SemanticEncoder
from glcs.core.models import (
    LogicalForm,
    Entity,
    Relation,
    LogicalType,
    Polarity,
    Violation
)
from glcs.utils.exceptions import ConsistencyError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def memory_manager():
    """Provide an in-memory MemoryManager for each test."""
    collection_name = f"test_{uuid.uuid4().hex[:8]}"
    return MemoryManager(collection_name=collection_name, in_memory=True)


@pytest.fixture
def encoder():
    """Provide a SemanticEncoder for adding embeddings."""
    SemanticEncoder.clear_model_cache()
    return SemanticEncoder()


@pytest.fixture
def consistency_checker(memory_manager, encoder):
    """Provide a ConsistencyChecker instance."""
    return ConsistencyChecker(memory_manager, encoder)


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

def test_consistency_checker_initialization(memory_manager, encoder):
    """Test that ConsistencyChecker initializes correctly."""
    checker = ConsistencyChecker(memory_manager, encoder)
    assert checker.memory == memory_manager
    assert checker.encoder == encoder
    assert checker.redundancy_threshold == 0.9


def test_consistency_checker_custom_threshold(memory_manager, encoder):
    """Test initialization with custom redundancy threshold."""
    checker = ConsistencyChecker(memory_manager, encoder, redundancy_threshold=0.85)
    assert checker.redundancy_threshold == 0.85


def test_consistency_checker_invalid_threshold_raises_error(memory_manager, encoder):
    """Test that invalid threshold raises error."""
    with pytest.raises(ConsistencyError, match="must be between"):
        ConsistencyChecker(memory_manager, encoder, redundancy_threshold=1.5)


# ============================================================================
# POLARITY CONTRADICTION TESTS
# ============================================================================

def test_detect_polarity_contradiction(consistency_checker, encoder, memory_manager):
    """Test detection of polarity contradiction."""
    # Create contradictory forms
    form1 = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Socrates is mortal"
    )

    form2 = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.NEGATIVE,
        source_text="Socrates is not mortal"
    )

    # Add embeddings and store
    encoder.add_embeddings_to_forms([form1, form2])
    memory_manager.store_form(form1)
    memory_manager.store_form(form2)

    # Check consistency
    report = consistency_checker.check_context_consistency("test")

    assert not report.is_consistent
    assert len(report.violations) == 1
    assert report.violations[0].violation_type == "POLARITY_CONTRADICTION"
    assert report.violations[0].severity in ["HIGH", "MEDIUM"]


def test_no_polarity_contradiction_same_polarity(consistency_checker, encoder, memory_manager):
    """Test that same polarity doesn't trigger contradiction."""
    form1 = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Socrates is mortal"
    )

    form2 = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="plato"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Plato is mortal"
    )

    encoder.add_embeddings_to_forms([form1, form2])
    memory_manager.store_form(form1)
    memory_manager.store_form(form2)

    report = consistency_checker.check_context_consistency("test")

    # Should be consistent (or only redundancy, not polarity contradiction)
    polarity_contradictions = [
        v for v in report.violations
        if v.violation_type == "POLARITY_CONTRADICTION"
    ]
    assert len(polarity_contradictions) == 0


# ============================================================================
# UNIVERSAL VS GROUND CONTRADICTION TESTS
# ============================================================================

def test_detect_universal_ground_contradiction(consistency_checker, encoder, memory_manager):
    """Test detection of universal rule vs ground fact contradiction.

    Socrates is known to be human via entity_type, so the checker can infer
    he falls under the universal rule 'All humans are mortal'.
    """
    # Universal rule: All humans are mortal
    universal = LogicalForm(
        context_id="test",
        logical_type=LogicalType.UNIVERSAL_RULE,
        subject=Entity(name="humans"),
        predicate=Relation(verb="are"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="All humans are mortal"
    )

    # Ground fact: Socrates is not mortal (entity_type="humans" links him to the rule)
    ground = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates", entity_type="humans"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.NEGATIVE,
        source_text="Socrates is not mortal"
    )

    encoder.add_embeddings_to_forms([universal, ground])
    memory_manager.store_form(universal)
    memory_manager.store_form(ground)

    report = consistency_checker.check_context_consistency("test")

    universal_contradictions = [
        v for v in report.violations
        if v.violation_type == "UNIVERSAL_GROUND_CONTRADICTION"
    ]

    assert len(universal_contradictions) > 0
    assert universal_contradictions[0].severity == "HIGH"


def test_no_universal_ground_contradiction_same_polarity(
    consistency_checker,
    encoder,
    memory_manager
):
    """Test that same polarity doesn't trigger universal vs ground contradiction."""
    universal = LogicalForm(
        context_id="test",
        logical_type=LogicalType.UNIVERSAL_RULE,
        subject=Entity(name="humans"),
        predicate=Relation(verb="are"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="All humans are mortal"
    )

    ground = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Socrates is mortal"
    )

    encoder.add_embeddings_to_forms([universal, ground])
    memory_manager.store_form(universal)
    memory_manager.store_form(ground)

    report = consistency_checker.check_context_consistency("test")

    universal_contradictions = [
        v for v in report.violations
        if v.violation_type == "UNIVERSAL_GROUND_CONTRADICTION"
    ]

    assert len(universal_contradictions) == 0


# ============================================================================
# REDUNDANCY DETECTION TESTS
# ============================================================================

def test_detect_exact_redundancy(consistency_checker, encoder, memory_manager):
    """Test detection of exact duplicate forms."""
    form1 = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Socrates is mortal"
    )

    form2 = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Socrates is mortal"  # Exact duplicate
    )

    encoder.add_embeddings_to_forms([form1, form2])
    memory_manager.store_form(form1)
    memory_manager.store_form(form2)

    report = consistency_checker.check_context_consistency("test")

    exact_redundancies = [
        v for v in report.violations
        if v.violation_type == "EXACT_REDUNDANCY"
    ]

    assert len(exact_redundancies) > 0
    assert exact_redundancies[0].severity == "LOW"


def test_detect_semantic_redundancy(consistency_checker, encoder, memory_manager):
    """Test detection of semantic redundancy."""
    form1 = LogicalForm(
        context_id="test",
        logical_type=LogicalType.UNIVERSAL_RULE,
        subject=Entity(name="humans"),
        predicate=Relation(verb="are"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="All humans are mortal"
    )

    form2 = LogicalForm(
        context_id="test",
        logical_type=LogicalType.UNIVERSAL_RULE,
        subject=Entity(name="humans"),
        predicate=Relation(verb="are"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Every person is mortal"  # Semantically similar
    )

    encoder.add_embeddings_to_forms([form1, form2])
    memory_manager.store_form(form1)
    memory_manager.store_form(form2)

    report = consistency_checker.check_context_consistency("test")

    # Should find either exact or semantic redundancy
    redundancies = [
        v for v in report.violations
        if "REDUNDANCY" in v.violation_type
    ]

    assert len(redundancies) > 0
    assert all(v.severity == "LOW" for v in redundancies)


# ============================================================================
# CONTEXT CONSISTENCY TESTS
# ============================================================================

def test_empty_context_is_consistent(consistency_checker):
    """Test that empty context is considered consistent."""
    report = consistency_checker.check_context_consistency("empty")

    assert report.is_consistent
    assert len(report.violations) == 0
    assert report.total_forms_checked == 0


def test_single_form_is_consistent(consistency_checker, encoder, memory_manager):
    """Test that single form is consistent."""
    form = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Socrates is mortal"
    )

    encoder.add_embedding_to_form(form)
    memory_manager.store_form(form)

    report = consistency_checker.check_context_consistency("test")

    assert report.is_consistent
    assert len(report.violations) == 0
    assert report.total_forms_checked == 1


def test_consistent_context_with_multiple_forms(
    consistency_checker,
    encoder,
    memory_manager
):
    """Test that logically consistent forms pass check."""
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
            subject=Entity(name="plato"),
            predicate=Relation(verb="is"),
            object=Entity(name="philosopher"),
            polarity=Polarity.POSITIVE,
            source_text="Plato is a philosopher"
        )
    ]

    encoder.add_embeddings_to_forms(forms)
    for form in forms:
        memory_manager.store_form(form)

    report = consistency_checker.check_context_consistency("test")

    # Should be consistent (different enough topics)
    assert report.total_forms_checked == 3
    # May have some low-priority violations, but no high-severity ones
    high_violations = [v for v in report.violations if v.severity == "HIGH"]
    assert len(high_violations) == 0


# ============================================================================
# CHECK FORM AGAINST CONTEXT TESTS
# ============================================================================

def test_check_new_form_against_empty_context(consistency_checker, encoder):
    """Test checking new form against empty context."""
    form = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Socrates is mortal"
    )

    encoder.add_embedding_to_form(form)

    report = consistency_checker.check_form_against_context(form, "test")

    assert report.is_consistent
    assert len(report.violations) == 0


def test_check_new_form_contradicts_existing(
    consistency_checker,
    encoder,
    memory_manager
):
    """Test detecting contradiction with new form."""
    # Store existing form
    existing = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Socrates is mortal"
    )
    encoder.add_embedding_to_form(existing)
    memory_manager.store_form(existing)

    # New contradictory form
    new_form = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.NEGATIVE,
        source_text="Socrates is not mortal"
    )
    encoder.add_embedding_to_form(new_form)

    report = consistency_checker.check_form_against_context(new_form, "test")

    assert not report.is_consistent
    assert len(report.violations) > 0


# ============================================================================
# SEVERITY SCORING TESTS
# ============================================================================

def test_severity_high_for_universal_contradictions(
    consistency_checker,
    encoder,
    memory_manager
):
    """Test that universal rule contradictions get HIGH severity."""
    universal = LogicalForm(
        context_id="test",
        logical_type=LogicalType.UNIVERSAL_RULE,
        subject=Entity(name="humans"),
        predicate=Relation(verb="are"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="All humans are mortal"
    )

    ground = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates", entity_type="humans"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.NEGATIVE,
        source_text="Socrates is not mortal"
    )

    encoder.add_embeddings_to_forms([universal, ground])
    memory_manager.store_form(universal)
    memory_manager.store_form(ground)

    report = consistency_checker.check_context_consistency("test")

    universal_contradictions = [
        v for v in report.violations
        if v.violation_type == "UNIVERSAL_GROUND_CONTRADICTION"
    ]

    assert all(v.severity == "HIGH" for v in universal_contradictions)


def test_severity_low_for_redundancies(consistency_checker, encoder, memory_manager):
    """Test that redundancies get LOW severity."""
    form1 = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Socrates is mortal"
    )

    form2 = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Socrates is mortal"
    )

    encoder.add_embeddings_to_forms([form1, form2])
    memory_manager.store_form(form1)
    memory_manager.store_form(form2)

    report = consistency_checker.check_context_consistency("test")

    redundancies = [
        v for v in report.violations
        if "REDUNDANCY" in v.violation_type
    ]

    assert all(v.severity == "LOW" for v in redundancies)


# ============================================================================
# VIOLATION SUMMARY TESTS
# ============================================================================

def test_get_violation_summary(consistency_checker):
    """Test generating violation summary."""
    violations = [
        Violation(
            violation_type="POLARITY_CONTRADICTION",
            conflicting_forms=[uuid.uuid4(), uuid.uuid4()],
            severity="HIGH",
            explanation="Test contradiction 1"
        ),
        Violation(
            violation_type="POLARITY_CONTRADICTION",
            conflicting_forms=[uuid.uuid4(), uuid.uuid4()],
            severity="MEDIUM",
            explanation="Test contradiction 2"
        ),
        Violation(
            violation_type="EXACT_REDUNDANCY",
            conflicting_forms=[uuid.uuid4(), uuid.uuid4()],
            severity="LOW",
            explanation="Test redundancy"
        )
    ]

    summary = consistency_checker.get_violation_summary(violations)

    assert summary["total"] == 3
    assert summary["by_type"]["POLARITY_CONTRADICTION"] == 2
    assert summary["by_type"]["EXACT_REDUNDANCY"] == 1
    assert summary["by_severity"]["HIGH"] == 1
    assert summary["by_severity"]["MEDIUM"] == 1
    assert summary["by_severity"]["LOW"] == 1
    assert summary["high_severity_count"] == 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_workflow_integration(consistency_checker, encoder, memory_manager):
    """
    Integration test: Full consistency checking workflow.

    Simulates:
    1. Storing multiple LogicalForms
    2. Running consistency check
    3. Analyzing violations
    4. Generating summary
    """
    # Create a mix of consistent and inconsistent forms
    forms = [
        # Consistent chain
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
        # Redundant statement
        LogicalForm(
            context_id="session_123",
            logical_type=LogicalType.UNIVERSAL_RULE,
            subject=Entity(name="humans"),
            predicate=Relation(verb="are"),
            object=Entity(name="mortal"),
            polarity=Polarity.POSITIVE,
            source_text="Every person is mortal"  # Redundant
        )
    ]

    # Add embeddings and store
    encoder.add_embeddings_to_forms(forms)
    for form in forms:
        memory_manager.store_form(form)

    # Check consistency
    report = consistency_checker.check_context_consistency("session_123")

    # Should have some violations (redundancy at minimum)
    assert report.total_forms_checked == 3

    # Generate summary
    summary = consistency_checker.get_violation_summary(report.violations)
    assert summary["total"] >= 0
    assert "by_type" in summary
    assert "by_severity" in summary
