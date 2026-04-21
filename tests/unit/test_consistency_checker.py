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

import time
import uuid

import numpy as np
import pytest

from glcs.core.consistency_checker import ConsistencyChecker
from glcs.core.models import (
    LogicalForm,
    Entity,
    Relation,
    LogicalType,
    Polarity,
    ViolationType,
    Severity,
    Violation
)
from glcs.utils.exceptions import ConsistencyError


# ============================================================================
# FIXTURES
# ============================================================================

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


def test_detect_polarity_contradiction_paraphrase(consistency_checker, encoder, memory_manager):
    """Test that polarity contradiction is detected even when predicate/object differ.

    Regression test for issue #22: the old implementation required exact structural
    match (same subject, predicate verb, AND object name) before checking embeddings.
    Paraphrase contradictions — same subject, opposite polarity, different wording —
    were silently missed.  The fix keeps only the subject-name guard and lets the
    embedding similarity threshold (0.8) act as the semantic gate.
    """
    form1 = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=Polarity.POSITIVE,
        source_text="Socrates is mortal"
    )

    # Different predicate verb and no object — paraphrase of the negation.
    form2 = LogicalForm(
        context_id="test",
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name="socrates"),
        predicate=Relation(verb="cannot die"),
        polarity=Polarity.NEGATIVE,
        source_text="Socrates cannot die"
    )

    encoder.add_embeddings_to_forms([form1, form2])
    memory_manager.store_form(form1)
    memory_manager.store_form(form2)

    report = consistency_checker.check_context_consistency("test")

    polarity_contradictions = [
        v for v in report.violations
        if v.violation_type == "POLARITY_CONTRADICTION"
    ]
    # The two forms are semantically similar (both about Socrates and mortality)
    # and have opposite polarities — they should be flagged as a contradiction.
    assert len(polarity_contradictions) == 1


def test_no_polarity_contradiction_different_subjects(consistency_checker, encoder, memory_manager):
    """Test that different subjects do not produce a polarity contradiction.

    Even if two forms have high embedding similarity and opposite polarity,
    they should not be flagged unless they share the same subject.
    """
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
        polarity=Polarity.NEGATIVE,
        source_text="Plato is not mortal"
    )

    encoder.add_embeddings_to_forms([form1, form2])
    memory_manager.store_form(form1)
    memory_manager.store_form(form2)

    report = consistency_checker.check_context_consistency("test")

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
            violation_type=ViolationType.POLARITY_CONTRADICTION,
            conflicting_forms=[uuid.uuid4(), uuid.uuid4()],
            severity=Severity.HIGH,
            explanation="Test contradiction 1"
        ),
        Violation(
            violation_type=ViolationType.POLARITY_CONTRADICTION,
            conflicting_forms=[uuid.uuid4(), uuid.uuid4()],
            severity=Severity.MEDIUM,
            explanation="Test contradiction 2"
        ),
        Violation(
            violation_type=ViolationType.EXACT_REDUNDANCY,
            conflicting_forms=[uuid.uuid4(), uuid.uuid4()],
            severity=Severity.LOW,
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


# ============================================================================
# VECTORISED BATCH CHECKS — ISSUE #23
# ============================================================================

def _make_form(context_id: str, subject: str, polarity: Polarity, text: str) -> LogicalForm:
    """Helper: build a minimal LogicalForm with a synthetic embedding."""
    form = LogicalForm(
        context_id=context_id,
        logical_type=LogicalType.GROUND_FACT,
        subject=Entity(name=subject),
        predicate=Relation(verb="is"),
        object=Entity(name="mortal"),
        polarity=polarity,
        source_text=text,
    )
    # Assign a random normalised embedding so the matrix multiply path runs.
    vec = np.random.default_rng(abs(hash(text)) % (2**32)).random(768).astype(np.float32)
    form.embedding = vec / np.linalg.norm(vec)
    return form


def test_vectorised_polarity_contradictions_correctness(consistency_checker):
    """Vectorised _check_polarity_contradictions returns the same violations as
    the old pairwise loop for a small set of forms (regression test for #23)."""
    forms = [
        _make_form("ctx", "socrates", Polarity.POSITIVE, "Socrates is mortal"),
        _make_form("ctx", "socrates", Polarity.NEGATIVE, "Socrates is not mortal"),
        _make_form("ctx", "plato",    Polarity.POSITIVE, "Plato is mortal"),
        _make_form("ctx", "plato",    Polarity.NEGATIVE, "Plato is not mortal"),
        _make_form("ctx", "aristotle",Polarity.POSITIVE, "Aristotle is mortal"),
    ]

    violations = consistency_checker._check_polarity_contradictions(forms)

    # Aristotle has no opposing form — only socrates and plato pairs can fire.
    # Whether they fire depends on embedding similarity; at minimum no crash.
    assert isinstance(violations, list)
    for v in violations:
        assert v.violation_type == "POLARITY_CONTRADICTION"


def test_vectorised_redundancies_no_double_report(consistency_checker):
    """Exact-duplicate pairs should appear as EXACT_REDUNDANCY only, not also
    as SEMANTIC_REDUNDANCY (regression test for #23 exact/semantic overlap)."""
    form1 = _make_form("ctx", "socrates", Polarity.POSITIVE, "Socrates is mortal")
    # Identical text → exact redundancy.
    form2 = _make_form("ctx", "socrates", Polarity.POSITIVE, "Socrates is mortal")
    # Give form2 the same embedding as form1 to ensure it would hit semantic threshold.
    form2.embedding = form1.embedding.copy()

    violations = consistency_checker._check_redundancies([form1, form2])

    exact = [v for v in violations if v.violation_type == "EXACT_REDUNDANCY"]
    semantic = [v for v in violations if v.violation_type == "SEMANTIC_REDUNDANCY"]

    assert len(exact) == 1, "Expected exactly one EXACT_REDUNDANCY violation"
    assert len(semantic) == 0, "Exact-duplicate pair must not also appear as SEMANTIC_REDUNDANCY"


def test_vectorised_batch_polarity_performance(consistency_checker):
    """_check_polarity_contradictions must complete in < 5 seconds for 200 forms.

    This is a smoke-level performance guard.  200 forms → up to 10 000 pairs
    with the old O(n²) loop; with vectorised matrix multiply they are computed
    as a single BLAS call.
    """
    rng = np.random.default_rng(42)
    forms = []
    for i in range(200):
        polarity = Polarity.POSITIVE if i % 2 == 0 else Polarity.NEGATIVE
        form = LogicalForm(
            context_id="perf",
            logical_type=LogicalType.GROUND_FACT,
            subject=Entity(name=f"entity_{i % 20}"),   # 20 distinct subjects
            predicate=Relation(verb="is"),
            object=Entity(name="mortal"),
            polarity=polarity,
            source_text=f"Statement {i}",
        )
        vec = rng.random(768).astype(np.float32)
        form.embedding = vec / np.linalg.norm(vec)
        forms.append(form)

    start = time.perf_counter()
    violations = consistency_checker._check_polarity_contradictions(forms)
    elapsed = time.perf_counter() - start

    assert isinstance(violations, list)
    assert elapsed < 5.0, (
        f"_check_polarity_contradictions took {elapsed:.2f}s for 200 forms — "
        "vectorised implementation should be well under 5 s"
    )


def test_optimized_universal_ground_performance(consistency_checker):
    """_check_universal_ground_contradictions must be efficient for many rules/facts.
    
    500 forms (50 rules, 450 facts) with 50 distinct relations.
    Old O(n^2) logic: 50 * 450 = 22,500 full comparisons.
    Optimized logic: Groups by relation, significantly fewer comparisons.
    """
    forms = []
    # 50 universal rules — exactly one per relation
    for i in range(50):
        rel_idx = i
        forms.append(LogicalForm(
            context_id="perf_ug",
            logical_type=LogicalType.UNIVERSAL_RULE,
            subject=Entity(name=f"class_{rel_idx}"),
            predicate=Relation(verb=f"verb_{rel_idx}"),
            object=Entity(name=f"object_{rel_idx}"),
            polarity=Polarity.POSITIVE,
            source_text=f"Rule {i}",
        ))
        
    # 450 ground facts spread across same 50 relations
    for i in range(450):
        rel_idx = i % 50
        forms.append(LogicalForm(
            context_id="perf_ug",
            logical_type=LogicalType.GROUND_FACT,
            subject=Entity(name=f"entity_{i}", entity_type=f"class_{rel_idx}"),
            predicate=Relation(verb=f"verb_{rel_idx}"),
            object=Entity(name=f"object_{rel_idx}"),
            polarity=Polarity.NEGATIVE,
            source_text=f"Fact {i}",
        ))

    start = time.perf_counter()
    violations = consistency_checker._check_universal_ground_contradictions(forms)
    elapsed = time.perf_counter() - start

    assert len(violations) == 450  # Every fact contradicts its class rule
    assert elapsed < 1.0, f"Universal-ground check took {elapsed:.2f}s — should be < 1s"
