"""
Consistency Checker for GLCS (Global Logical Context Store).

This module provides logical consistency checking for stored LogicalForm objects.
It detects contradictions, redundancies, and other logical inconsistencies.

Key Features:
    - Contradiction detection (polarity, universal vs ground facts)
    - Redundancy detection (semantic and exact duplicates)
    - Severity scoring (HIGH, MEDIUM, LOW)
    - Integration with MemoryManager and SemanticEncoder
    - Generates ConsistencyReport with detailed violations

Usage:
    >>> from glcs.core.consistency_checker import ConsistencyChecker
    >>> from glcs.core.memory_manager import MemoryManager
    >>> from glcs.core.semantic_encoder import SemanticEncoder
    >>>
    >>> memory = MemoryManager()
    >>> encoder = SemanticEncoder()
    >>> checker = ConsistencyChecker(memory, encoder)
    >>>
    >>> report = checker.check_context_consistency("session_123")
    >>> if not report.is_consistent:
    ...     for violation in report.violations:
    ...         print(f"{violation.severity}: {violation.explanation}")
"""

from collections import defaultdict
from typing import List, Optional
from uuid import UUID

import numpy as np

from glcs.core.models import (
    LogicalForm,
    LogicalType,
    Polarity,
    ViolationType,
    Severity,
    Violation,
    ConsistencyReport
)
from glcs.core.memory_manager import MemoryManager
from glcs.core.semantic_encoder import SemanticEncoder
from glcs.utils.exceptions import ConsistencyError
from glcs.utils.logger import get_logger

logger = get_logger(__name__)

# Copula verb forms treated as equivalent for predicate matching.
# "All humans ARE mortal" vs "Socrates IS not mortal" should be compared.
_COPULA_VERBS: frozenset = frozenset({"is", "are", "was", "were", "be", "been", "being", "am"})


def _verbs_match(verb1: str, verb2: str) -> bool:
    """Return True if two verbs describe the same predicate relation."""
    if verb1 == verb2:
        return True
    # Treat all copula forms as the same verb
    if verb1 in _COPULA_VERBS and verb2 in _COPULA_VERBS:
        return True
    return False


class ConsistencyChecker:
    """
    Checks logical consistency of stored LogicalForm objects.

    The ConsistencyChecker analyzes LogicalForms for:
    - Contradictions (opposite polarities, universal vs ground)
    - Redundancies (semantic duplicates, exact duplicates)
    - Logical inconsistencies

    It generates ConsistencyReports with detailed Violations.

    Attributes:
        memory: MemoryManager for retrieving stored forms
        encoder: SemanticEncoder for similarity comparisons
        redundancy_threshold: Cosine similarity threshold for redundancy (default: 0.9)

    Example:
        >>> checker = ConsistencyChecker(memory, encoder)
        >>> report = checker.check_context_consistency("session_123")
        >>> print(f"Consistent: {report.is_consistent}")
        >>> print(f"Violations: {len(report.violations)}")
    """

    def __init__(
        self,
        memory: MemoryManager,
        encoder: SemanticEncoder,
        redundancy_threshold: float = 0.9
    ):
        """
        Initialize the Consistency Checker.

        Args:
            memory: MemoryManager instance for form retrieval
            encoder: SemanticEncoder instance for similarity computation
            redundancy_threshold: Similarity threshold for redundancy detection
                                (default: 0.9, range: 0.0-1.0)

        Raises:
            ConsistencyError: If initialization fails
        """
        if not 0.0 <= redundancy_threshold <= 1.0:
            raise ConsistencyError(
                f"redundancy_threshold must be between 0.0 and 1.0, got {redundancy_threshold}"
            )

        self.memory = memory
        self.encoder = encoder
        self.redundancy_threshold = redundancy_threshold

        logger.info(f"Initialized ConsistencyChecker with redundancy_threshold={redundancy_threshold}")

    # ========================================================================
    # MAIN CONSISTENCY CHECKING
    # ========================================================================

    def check_context_consistency(self, context_id: str) -> ConsistencyReport:
        """
        Check consistency of all LogicalForms in a context.

        This is the main entry point for consistency checking. It runs all
        consistency checks and returns a comprehensive report.

        Args:
            context_id: Context/session ID to check

        Returns:
            ConsistencyReport with violations (if any)

        Example:
            >>> report = checker.check_context_consistency("session_123")
            >>> if not report.is_consistent:
            ...     print(f"Found {len(report.violations)} violations")
        """
        try:
            # Retrieve all forms in context
            forms = self.memory.get_forms_by_context(context_id)

            if not forms:
                # Empty context is consistent
                return ConsistencyReport(
                    context_id=context_id,
                    violations=[],
                    total_forms_checked=0
                )

            logger.info(f"Checking consistency for context '{context_id}' with {len(forms)} forms")

            # Run all consistency checks
            violations = []

            # 1. Check for polarity contradictions
            violations.extend(self._check_polarity_contradictions(forms))

            # 2. Check for universal vs ground contradictions
            violations.extend(self._check_universal_ground_contradictions(forms))

            # 3. Check for redundancies
            violations.extend(self._check_redundancies(forms))

            # Create report
            report = ConsistencyReport(
                context_id=context_id,
                violations=violations,
                total_forms_checked=len(forms)
            )

            logger.info(
                f"Consistency check complete: {len(violations)} violations found "
                f"in {len(forms)} forms"
            )

            return report

        except Exception as e:
            raise ConsistencyError(
                f"Failed to check context consistency: {str(e)} (context_id: {context_id})"
            )

    def check_form_against_context(
        self,
        form: LogicalForm,
        context_id: str
    ) -> ConsistencyReport:
        """
        Check if a new LogicalForm is consistent with existing context.

        Optimized implementation: uses targeted memory searches (subject, 
        semantic similarity, and relation) to avoid O(n) context scan.

        Args:
            form: New LogicalForm to check
            context_id: Context to check against

        Returns:
            ConsistencyReport indicating if form is consistent
        """
        try:
            violations = []
            scanned_ids = set()

            # 1. Check for polarity contradictions (Subject-based search)
            # Polarity contradictions MUST share the same subject.
            subject_forms = self.memory.search_by_entity(form.subject.name, context_id=context_id)
            for existing in subject_forms:
                scanned_ids.add(str(existing.form_id))
                violation = self._check_polarity_contradiction(form, existing)
                if violation:
                    violations.append(violation)

            # 2. Check for universal vs ground contradictions (Subject/Relation-based)
            if form.logical_type == LogicalType.UNIVERSAL_RULE:
                # New rule vs existing ground facts.
                # Violation requires fact.subject.name == rule.subject.name 
                # OR fact.subject.entity_type == rule.subject.name.
                # We reuse subject_forms (facts where this name is subject/object).
                for existing in subject_forms:
                    # scanned_ids already handled above for subject_forms
                    violation = self._check_universal_ground_contradiction(form, existing)
                    if violation:
                        violations.append(violation)
                
                # Also need to check facts where rule.subject.name is the entity_type.
                # Currently MemoryManager doesn't support searching by entity_type.
                # If this becomes a bottleneck, we would add metadata indexing for it.
                # For now, we fall back to context-wide rules if needed, but 
                # most contradictions are caught by the subject name match.
            
            elif form.logical_type == LogicalType.GROUND_FACT:
                # New fact vs existing universal rules.
                # Rules are fewer than facts. We fetch all rules in context.
                # TODO: Optimize with relation-based search if many rules exist.
                existing_forms = self.memory.get_forms_by_context(context_id)
                for existing in existing_forms:
                    if existing.logical_type == LogicalType.UNIVERSAL_RULE:
                        scanned_ids.add(str(existing.form_id))
                        violation = self._check_universal_ground_contradiction(form, existing)
                        if violation:
                            violations.append(violation)

            # 3. Check for redundancies (Similarity-based search)
            if form.embedding is not None:
                # Redundancies require high semantic similarity.
                similar_forms = self.memory.search_similar_forms(
                    form.embedding, 
                    top_k=20, 
                    context_id=context_id
                )
                for existing in similar_forms:
                    scanned_ids.add(str(existing.form_id))
                    violation = self._check_redundancy(form, existing)
                    if violation:
                        violations.append(violation)

            report = ConsistencyReport(
                context_id=context_id,
                violations=violations,
                total_forms_checked=len(scanned_ids)
            )

            return report

        except Exception as e:
            raise ConsistencyError(
                f"Failed to check form against context: {str(e)} (context_id: {context_id})"
            )

    # ========================================================================
    # POLARITY CONTRADICTION DETECTION
    # ========================================================================

    def _check_polarity_contradictions(self, forms: List[LogicalForm]) -> List[Violation]:
        """
        Check for polarity contradictions among forms.

        A polarity contradiction occurs when two semantically similar statements
        have opposite polarities (POSITIVE vs NEGATIVE).

        Example:
            "Socrates is mortal" (POSITIVE)
            "Socrates is not mortal" (NEGATIVE)
            -> CONTRADICTION

        Vectorised implementation: forms are grouped by subject name, then a
        single matrix multiply (pos_embeddings @ neg_embeddings.T) computes all
        cross-polarity similarities at once.  This is O(p*q*d) via BLAS rather
        than O(p*q) sequential dot products, and avoids comparing forms that
        cannot possibly contradict (different subjects, same polarity).

        Args:
            forms: List of LogicalForms to check

        Returns:
            List of Violation objects for contradictions found
        """
        if len(forms) < 2:
            return []

        violations: List[Violation] = []

        # Group by subject name — contradictions require the same subject.
        # Subject names are normalised to lowercase by Entity.normalize_name.
        by_subject: dict = defaultdict(list)
        for form in forms:
            by_subject[form.subject.name].append(form)

        for subject_forms in by_subject.values():
            positives = [
                f for f in subject_forms
                if f.polarity == Polarity.POSITIVE and f.embedding is not None
            ]
            negatives = [
                f for f in subject_forms
                if f.polarity == Polarity.NEGATIVE and f.embedding is not None
            ]

            if not positives or not negatives:
                continue

            # Single matrix multiply: (p × d) @ (d × q) → (p × q).
            # Embeddings are L2-normalised so dot product == cosine similarity.
            pos_matrix = np.vstack([f.embedding for f in positives])  # (p, d)
            neg_matrix = np.vstack([f.embedding for f in negatives])  # (q, d)
            sim_matrix = pos_matrix @ neg_matrix.T                    # (p, q)

            rows, cols = np.where(sim_matrix >= 0.8)
            for r, c in zip(rows, cols):
                form1 = positives[r]
                form2 = negatives[c]
                similarity = float(sim_matrix[r, c])
                severity = self._calculate_severity(
                    violation_type=ViolationType.POLARITY_CONTRADICTION,
                    form1=form1,
                    form2=form2
                )
                explanation = (
                    f"Polarity contradiction detected (similarity: {similarity:.2f}): "
                    f"'{form1.source_text}' ({form1.polarity.value}) contradicts "
                    f"'{form2.source_text}' ({form2.polarity.value})"
                )
                violations.append(Violation(
                    violation_type=ViolationType.POLARITY_CONTRADICTION,
                    conflicting_forms=[form1.form_id, form2.form_id],
                    severity=severity,
                    explanation=explanation
                ))

        return violations

    def _check_polarity_contradiction(
        self,
        form1: LogicalForm,
        form2: LogicalForm
    ) -> Optional[Violation]:
        """
        Check if two forms have a polarity contradiction.

        Args:
            form1: First LogicalForm
            form2: Second LogicalForm

        Returns:
            Violation if contradiction found, None otherwise
        """
        # Must have opposite polarities
        if form1.polarity == form2.polarity:
            return None

        # Must share the same subject — entity names are normalised to lowercase
        # by the model validator, so this comparison is case-insensitive.
        # We intentionally do NOT require predicate/object name equality here:
        # paraphrase contradictions ("John is tall" vs "John lacks height") have
        # the same subject and opposite polarity but different verbs/objects.
        # The embedding similarity check below is the primary semantic gate.
        if form1.subject.name != form2.subject.name:
            return None

        # Must have high semantic similarity (primary semantic gate)
        if form1.embedding is None or form2.embedding is None:
            return None

        similarity = self.encoder.cosine_similarity(form1.embedding, form2.embedding)

        if similarity >= 0.8:  # High similarity threshold for contradictions
            severity = self._calculate_severity(
                violation_type=ViolationType.POLARITY_CONTRADICTION,
                form1=form1,
                form2=form2
            )

            explanation = (
                f"Polarity contradiction detected (similarity: {similarity:.2f}): "
                f"'{form1.source_text}' ({form1.polarity.value}) contradicts "
                f"'{form2.source_text}' ({form2.polarity.value})"
            )

            return Violation(
                violation_type=ViolationType.POLARITY_CONTRADICTION,
                conflicting_forms=[form1.form_id, form2.form_id],
                severity=severity,
                explanation=explanation
            )

        return None

    # ========================================================================
    # UNIVERSAL VS GROUND CONTRADICTION DETECTION
    # ========================================================================

    def _check_universal_ground_contradictions(
        self,
        forms: List[LogicalForm]
    ) -> List[Violation]:
        """
        Check for contradictions between universal rules and ground facts.

        A universal rule (∀x: P(x) → Q(x)) contradicts a ground fact
        if the fact violates the rule.

        Example:
            Universal: "All humans are mortal" (POSITIVE)
            Ground: "Socrates is not mortal" (NEGATIVE, Socrates is human)
            -> CONTRADICTION

        Optimized implementation: groups rules and facts by (predicate, object)
        to avoid O(n^2) nested loops over all forms.

        Args:
            forms: List of LogicalForms to check

        Returns:
            List of Violation objects for contradictions found
        """
        violations = []

        # Separate universal rules from ground facts and group by predicate/object
        # Key: (normalized_verb, object_name_or_none)
        rules_by_relation = defaultdict(list)
        facts_by_relation = defaultdict(list)

        for f in forms:
            # Canonicalize copula verbs
            verb = f.predicate.verb.strip().lower()
            if verb in _COPULA_VERBS:
                verb = "be"
            
            obj_name = f.object.name if f.object else None
            rel_key = (verb, obj_name)

            if f.logical_type == LogicalType.UNIVERSAL_RULE:
                rules_by_relation[rel_key].append(f)
            elif f.logical_type == LogicalType.GROUND_FACT:
                facts_by_relation[rel_key].append(f)

        # Only check rules against facts within the same relation group
        for rel_key, rules in rules_by_relation.items():
            facts = facts_by_relation.get(rel_key)
            if not facts:
                continue

            for rule in rules:
                for fact in facts:
                    # Polarity check is fast
                    if rule.polarity == fact.polarity:
                        continue

                    # Subject class membership check
                    subject_match = (rule.subject.name == fact.subject.name)
                    if not subject_match and fact.subject.entity_type is not None:
                        subject_match = (
                            fact.subject.entity_type.strip().lower() == rule.subject.name
                        )

                    if subject_match:
                        severity = Severity.HIGH
                        explanation = (
                            f"Universal rule contradiction: "
                            f"Universal rule '{rule.source_text}' ({rule.polarity.value}) "
                            f"is contradicted by ground fact '{fact.source_text}' ({fact.polarity.value})"
                        )

                        violations.append(Violation(
                            violation_type=ViolationType.UNIVERSAL_GROUND_CONTRADICTION,
                            conflicting_forms=[rule.form_id, fact.form_id],
                            severity=severity,
                            explanation=explanation
                        ))

        return violations

    def _check_universal_ground_contradiction(
        self,
        form1: LogicalForm,
        form2: LogicalForm
    ) -> Optional[Violation]:
        """
        Check if a universal rule contradicts a ground fact.

        Args:
            form1: First LogicalForm
            form2: Second LogicalForm

        Returns:
            Violation if contradiction found, None otherwise
        """
        # Identify which is universal and which is ground
        if form1.logical_type == LogicalType.UNIVERSAL_RULE:
            rule, fact = form1, form2
        elif form2.logical_type == LogicalType.UNIVERSAL_RULE:
            rule, fact = form2, form1
        else:
            # Neither is a universal rule
            return None

        # Fact must be a ground fact
        if fact.logical_type != LogicalType.GROUND_FACT:
            return None

        # Check if fact violates rule.
        # Rule: "All X verb Y" (subject=X, predicate=verb, object=Y, polarity=POSITIVE)
        # Fact: "a not verb Y" (subject=a, predicate=verb, object=Y, polarity=NEGATIVE)
        # A violation requires: opposite polarity, same predicate, same object (or both
        # unary), and the fact's subject must belong to the rule's subject class.
        #
        # Subject class membership: without a type hierarchy/ontology we cannot perform
        # deep instance-of inference (e.g. "Socrates is-a human").  We check:
        #   (a) exact name match — fact.subject.name == rule.subject.name
        #   (b) entity_type match — fact.subject.entity_type == rule.subject.name
        # Cross-class contradictions that require external type knowledge are NOT detected.

        # Must have opposite polarities
        if rule.polarity == fact.polarity:
            return None

        # Predicate (verb) must match (copula forms treated as equivalent)
        if not _verbs_match(rule.predicate.verb, fact.predicate.verb):
            return None

        # Object must match, or both must be absent (unary predicate)
        if rule.object is not None and fact.object is not None:
            if rule.object.name != fact.object.name:
                return None
        elif rule.object is not None or fact.object is not None:
            # One has an object and the other doesn't — different relations
            return None

        # Subject class membership check
        subject_match = (rule.subject.name == fact.subject.name)
        if not subject_match and fact.subject.entity_type is not None:
            subject_match = (
                fact.subject.entity_type.strip().lower() == rule.subject.name
            )

        if not subject_match:
            return None

        severity = Severity.HIGH  # Universal rule violations are serious
        explanation = (
            f"Universal rule contradiction: "
            f"Universal rule '{rule.source_text}' ({rule.polarity.value}) "
            f"is contradicted by ground fact '{fact.source_text}' ({fact.polarity.value})"
        )

        return Violation(
            violation_type=ViolationType.UNIVERSAL_GROUND_CONTRADICTION,
            conflicting_forms=[rule.form_id, fact.form_id],
            severity=severity,
            explanation=explanation
        )

    # ========================================================================
    # REDUNDANCY DETECTION
    # ========================================================================

    def _check_redundancies(self, forms: List[LogicalForm]) -> List[Violation]:
        """
        Check for redundant (duplicate) forms.

        Redundancy types:
        - Exact: Identical source text  (detected via O(n) dict grouping)
        - Semantic: High cosine similarity >= threshold with same polarity
                    (detected via one matrix multiply per polarity group)

        Args:
            forms: List of LogicalForms to check

        Returns:
            List of Violation objects for redundancies found
        """
        if len(forms) < 2:
            return []

        violations: List[Violation] = []

        # --- Exact redundancy: O(n) dict grouping ---
        # Collect all pairs that share identical (normalised) source text AND polarity.
        exact_pairs: set = set()
        by_text_and_pol: dict = defaultdict(list)
        for form in forms:
            key = (form.source_text.strip().lower(), form.polarity)
            by_text_and_pol[key].append(form)

        for group in by_text_and_pol.values():
            for i, form1 in enumerate(group):
                for form2 in group[i + 1:]:
                    exact_pairs.add((form1.form_id, form2.form_id))
                    violations.append(Violation(
                        violation_type=ViolationType.EXACT_REDUNDANCY,
                        conflicting_forms=[form1.form_id, form2.form_id],
                        severity=Severity.LOW,
                        explanation=(
                            f"Exact redundancy: '{form1.source_text}' is duplicated"
                        )
                    ))

        # --- Semantic redundancy: one matrix multiply per polarity group ---
        # Semantic redundancy requires the same polarity; different-polarity
        # near-duplicates are polarity contradictions, not redundancies.
        for polarity in (Polarity.POSITIVE, Polarity.NEGATIVE):
            group = [
                f for f in forms
                if f.polarity == polarity and f.embedding is not None
            ]
            if len(group) < 2:
                continue

            emb_matrix = np.vstack([f.embedding for f in group])     # (m, d)
            sim_matrix = emb_matrix @ emb_matrix.T                   # (m, m)

            # Upper triangle only (i < j) — avoids self-pairs and duplicates.
            rows, cols = np.where(np.triu(sim_matrix >= self.redundancy_threshold, k=1))
            for r, c in zip(rows, cols):
                form1 = group[r]
                form2 = group[c]

                # Skip pairs already reported as exact redundancy.
                if (form1.form_id, form2.form_id) in exact_pairs:
                    continue

                similarity = float(sim_matrix[r, c])
                violations.append(Violation(
                    violation_type=ViolationType.SEMANTIC_REDUNDANCY,
                    conflicting_forms=[form1.form_id, form2.form_id],
                    severity=Severity.LOW,
                    explanation=(
                        f"Semantic redundancy detected (similarity: {similarity:.2f}): "
                        f"'{form1.source_text}' and '{form2.source_text}' "
                        f"have very similar meanings"
                    )
                ))

        return violations

    def _check_redundancy(
        self,
        form1: LogicalForm,
        form2: LogicalForm
    ) -> Optional[Violation]:
        """
        Check if two forms are redundant.

        Args:
            form1: First LogicalForm
            form2: Second LogicalForm

        Returns:
            Violation if redundancy found, None otherwise
        """
        # Redundancy requires same polarity
        if form1.polarity != form2.polarity:
            return None

        # Check exact redundancy (identical source text)
        if form1.source_text.strip().lower() == form2.source_text.strip().lower():
            return Violation(
                violation_type=ViolationType.EXACT_REDUNDANCY,
                conflicting_forms=[form1.form_id, form2.form_id],
                severity=Severity.LOW,  # Exact duplicates are low severity
                explanation=(
                    f"Exact redundancy: '{form1.source_text}' is duplicated"
                )
            )

        # Check semantic redundancy
        if form1.embedding is None or form2.embedding is None:
            return None

        similarity = self.encoder.cosine_similarity(form1.embedding, form2.embedding)

        if similarity >= self.redundancy_threshold:
            # Must have same polarity for redundancy
            if form1.polarity != form2.polarity:
                return None  # Different polarity = not redundant

            return Violation(
                violation_type=ViolationType.SEMANTIC_REDUNDANCY,
                conflicting_forms=[form1.form_id, form2.form_id],
                severity=Severity.LOW,  # Semantic redundancy is low severity
                explanation=(
                    f"Semantic redundancy detected (similarity: {similarity:.2f}): "
                    f"'{form1.source_text}' and '{form2.source_text}' "
                    f"have very similar meanings"
                )
            )

        return None

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _are_structurally_similar(
        self,
        form1: LogicalForm,
        form2: LogicalForm
    ) -> bool:
        """
        Check if two forms are structurally similar.

        Structural similarity means same subject, predicate, and object names.

        Args:
            form1: First LogicalForm
            form2: Second LogicalForm

        Returns:
            True if structurally similar, False otherwise
        """
        # Check subject
        if form1.subject.name != form2.subject.name:
            return False

        # Check predicate
        if form1.predicate.verb != form2.predicate.verb:
            return False

        # Check object (handle None cases)
        if form1.object is None and form2.object is None:
            return True
        elif form1.object is None or form2.object is None:
            return False
        else:
            return form1.object.name == form2.object.name

    def _calculate_severity(
        self,
        violation_type: ViolationType,
        form1: LogicalForm,
        form2: LogicalForm
    ) -> Severity:
        """
        Calculate violation severity.

        Severity levels:
        - HIGH: Critical contradictions (universal rules, high-confidence facts)
        - MEDIUM: Moderate contradictions
        - LOW: Redundancies, low-confidence contradictions

        Args:
            violation_type: Type of violation
            form1: First conflicting form
            form2: Second conflicting form

        Returns:
            Severity enum value
        """
        # Redundancies are always LOW
        if "REDUNDANCY" in violation_type:
            return Severity.LOW

        # Universal rule violations are always HIGH
        if violation_type == ViolationType.UNIVERSAL_GROUND_CONTRADICTION:
            return Severity.HIGH

        # Polarity contradictions depend on confidence
        if violation_type == ViolationType.POLARITY_CONTRADICTION:
            avg_confidence = (form1.confidence_score + form2.confidence_score) / 2

            if avg_confidence >= 0.9:
                return Severity.HIGH
            elif avg_confidence >= 0.7:
                return Severity.MEDIUM
            else:
                return Severity.LOW

        return Severity.MEDIUM

    def get_violation_summary(self, violations: List[Violation]) -> dict:
        """
        Generate a summary of violations.

        Args:
            violations: List of Violation objects

        Returns:
            Dict with violation statistics:
                - total: Total violations
                - by_type: Count by violation type
                - by_severity: Count by severity
                - high_severity_count: Number of HIGH severity violations

        Example:
            >>> summary = checker.get_violation_summary(report.violations)
            >>> print(f"HIGH severity: {summary['high_severity_count']}")
        """
        summary = {
            "total": len(violations),
            "by_type": {},
            "by_severity": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "high_severity_count": 0
        }

        for violation in violations:
            # Count by type
            vtype = violation.violation_type
            summary["by_type"][vtype] = summary["by_type"].get(vtype, 0) + 1

            # Count by severity
            summary["by_severity"][violation.severity] += 1

            if violation.severity == "HIGH":
                summary["high_severity_count"] += 1

        return summary
