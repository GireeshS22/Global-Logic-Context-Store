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

from typing import List, Optional, Tuple
from uuid import UUID

from glcs.core.models import (
    LogicalForm,
    LogicalType,
    Polarity,
    Violation,
    ConsistencyReport
)
from glcs.core.memory_manager import MemoryManager
from glcs.core.semantic_encoder import SemanticEncoder
from glcs.utils.exceptions import ConsistencyError
from glcs.utils.logger import get_logger

logger = get_logger(__name__)


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
                    is_consistent=True,
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
                is_consistent=(len(violations) == 0),
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

        This is useful for validating new statements before adding them
        to the knowledge base.

        Args:
            form: New LogicalForm to check
            context_id: Context to check against

        Returns:
            ConsistencyReport indicating if form is consistent

        Example:
            >>> new_form = LogicalForm(...)
            >>> encoder.add_embedding_to_form(new_form)
            >>> report = checker.check_form_against_context(new_form, "session_123")
            >>> if report.is_consistent:
            ...     memory.store_form(new_form)
        """
        try:
            # Get existing forms in context
            existing_forms = self.memory.get_forms_by_context(context_id)

            if not existing_forms:
                # No existing forms, new form is consistent
                return ConsistencyReport(
                    context_id=context_id,
                    is_consistent=True,
                    violations=[],
                    total_forms_checked=1
                )

            violations = []

            # Check new form against each existing form
            for existing_form in existing_forms:
                # Check polarity contradiction
                violation = self._check_polarity_contradiction(form, existing_form)
                if violation:
                    violations.append(violation)

                # Check universal vs ground contradiction
                violation = self._check_universal_ground_contradiction(form, existing_form)
                if violation:
                    violations.append(violation)

                # Check redundancy
                violation = self._check_redundancy(form, existing_form)
                if violation:
                    violations.append(violation)

            report = ConsistencyReport(
                context_id=context_id,
                is_consistent=(len(violations) == 0),
                violations=violations,
                total_forms_checked=len(existing_forms) + 1
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

        Args:
            forms: List of LogicalForms to check

        Returns:
            List of Violation objects for contradictions found
        """
        violations = []

        for i, form1 in enumerate(forms):
            for form2 in forms[i+1:]:
                violation = self._check_polarity_contradiction(form1, form2)
                if violation:
                    violations.append(violation)

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

        # Must be semantically similar (same subject, predicate, object)
        if not self._are_structurally_similar(form1, form2):
            return None

        # Must have high semantic similarity
        if form1.embedding is None or form2.embedding is None:
            return None

        similarity = self.encoder.cosine_similarity(form1.embedding, form2.embedding)

        if similarity >= 0.8:  # High similarity threshold for contradictions
            severity = self._calculate_severity(
                violation_type="POLARITY_CONTRADICTION",
                form1=form1,
                form2=form2
            )

            explanation = (
                f"Polarity contradiction detected (similarity: {similarity:.2f}): "
                f"'{form1.source_text}' ({form1.polarity.value}) contradicts "
                f"'{form2.source_text}' ({form2.polarity.value})"
            )

            return Violation(
                violation_type="POLARITY_CONTRADICTION",
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

        Args:
            forms: List of LogicalForms to check

        Returns:
            List of Violation objects for contradictions found
        """
        violations = []

        # Separate universal rules from ground facts
        universal_rules = [
            f for f in forms
            if f.logical_type == LogicalType.UNIVERSAL_RULE
        ]
        ground_facts = [
            f for f in forms
            if f.logical_type == LogicalType.GROUND_FACT
        ]

        # Check each universal rule against each ground fact
        for rule in universal_rules:
            for fact in ground_facts:
                violation = self._check_universal_ground_contradiction(rule, fact)
                if violation:
                    violations.append(violation)

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

        # Check if fact violates rule
        # Rule: "All X are Y" (subject=X, object=Y, polarity=POSITIVE)
        # Fact: "a is not Y" (object=Y, polarity=NEGATIVE) where 'a' is an X
        # This is a simplified check - full implementation would need
        # to verify that 'a' is indeed an instance of X

        # Must have opposite polarities
        if rule.polarity == fact.polarity:
            return None

        # Check if fact's object matches rule's object (same category)
        if rule.object and fact.object:
            if rule.object.name == fact.object.name:
                # Potential violation
                severity = "HIGH"  # Universal rule violations are serious

                explanation = (
                    f"Universal rule contradiction: "
                    f"Universal rule '{rule.source_text}' ({rule.polarity.value}) "
                    f"is contradicted by ground fact '{fact.source_text}' ({fact.polarity.value})"
                )

                return Violation(
                    violation_type="UNIVERSAL_GROUND_CONTRADICTION",
                    conflicting_forms=[rule.form_id, fact.form_id],
                    severity=severity,
                    explanation=explanation
                )

        return None

    # ========================================================================
    # REDUNDANCY DETECTION
    # ========================================================================

    def _check_redundancies(self, forms: List[LogicalForm]) -> List[Violation]:
        """
        Check for redundant (duplicate) forms.

        Redundancy types:
        - Exact: Identical source text
        - Semantic: High cosine similarity (>= threshold)

        Args:
            forms: List of LogicalForms to check

        Returns:
            List of Violation objects for redundancies found
        """
        violations = []

        for i, form1 in enumerate(forms):
            for form2 in forms[i+1:]:
                violation = self._check_redundancy(form1, form2)
                if violation:
                    violations.append(violation)

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
        # Check exact redundancy (identical source text)
        if form1.source_text.strip().lower() == form2.source_text.strip().lower():
            return Violation(
                violation_type="EXACT_REDUNDANCY",
                conflicting_forms=[form1.form_id, form2.form_id],
                severity="LOW",  # Exact duplicates are low severity
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
                violation_type="SEMANTIC_REDUNDANCY",
                conflicting_forms=[form1.form_id, form2.form_id],
                severity="LOW",  # Semantic redundancy is low severity
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
        violation_type: str,
        form1: LogicalForm,
        form2: LogicalForm
    ) -> str:
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
            Severity level: "HIGH", "MEDIUM", or "LOW"
        """
        # Redundancies are always LOW
        if "REDUNDANCY" in violation_type:
            return "LOW"

        # Universal rule violations are always HIGH
        if violation_type == "UNIVERSAL_GROUND_CONTRADICTION":
            return "HIGH"

        # Polarity contradictions depend on confidence
        if violation_type == "POLARITY_CONTRADICTION":
            avg_confidence = (form1.confidence_score + form2.confidence_score) / 2

            if avg_confidence >= 0.9:
                return "HIGH"
            elif avg_confidence >= 0.7:
                return "MEDIUM"
            else:
                return "LOW"

        # Default to MEDIUM
        return "MEDIUM"

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
