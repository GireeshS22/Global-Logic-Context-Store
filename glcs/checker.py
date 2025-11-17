"""
Consistency checking logic for logical statements.
"""

from typing import List, Tuple, Optional
from glcs.core import LogicalStatement, LogicalType
from glcs.memory import SimpleMemory


class ConsistencyChecker:
    """Check logical consistency of statements

    This checker validates new statements against stored knowledge
    to detect contradictions and logical violations.
    """

    def __init__(self, memory: SimpleMemory):
        """Initialize the consistency checker

        Args:
            memory: The memory store to check against
        """
        self.memory = memory

    def check_consistency(self, statement: LogicalStatement) -> Tuple[bool, float, List[str]]:
        """Check if statement is consistent with memory

        Args:
            statement: The statement to check

        Returns:
            Tuple of (is_consistent, confidence_score, violations)
            - is_consistent: True if no contradictions found
            - confidence_score: Confidence in the consistency check (0-1)
            - violations: List of human-readable violation messages
        """
        violations = []

        # Find direct conflicts
        conflicts = self.memory.find_conflicts(statement)
        for conflict in conflicts:
            violations.append(
                f"Contradicts: '{conflict.raw_text}'"
            )

        # Check logical implications
        if statement.type == LogicalType.GROUND:
            implications = self._check_implications(statement)
            violations.extend(implications)

        # Check conditional chains
        if statement.type == LogicalType.CONDITIONAL:
            conditional_violations = self._check_conditional_chains(statement)
            violations.extend(conditional_violations)

        # Calculate confidence score
        if violations:
            # Low confidence if contradictions found
            # Scale based on number of violations
            confidence = max(0.1, 1.0 - (len(violations) * 0.2))
        else:
            confidence = statement.confidence

        is_consistent = len(violations) == 0

        return is_consistent, confidence, violations

    def _check_implications(self, statement: LogicalStatement) -> List[str]:
        """Check if statement violates logical implications

        Args:
            statement: A ground fact to check

        Returns:
            List of violation messages
        """
        violations = []

        # Check against universal rules
        universals = self.memory.query(type=LogicalType.UNIVERSAL)
        for universal in universals:
            # Check if statement is an instance of the universal's subject
            if self.memory._is_instance_of(statement.subject, universal.subject):
                # Check for predicate conflicts
                if statement.predicate.startswith("not_") and \
                   universal.predicate == statement.predicate[4:]:
                    violations.append(
                        f"Violates universal rule: '{universal.raw_text}'"
                    )
                elif universal.predicate.startswith("not_") and \
                     statement.predicate == universal.predicate[4:]:
                    violations.append(
                        f"Violates universal rule: '{universal.raw_text}'"
                    )
                elif statement.predicate.startswith("is_") and \
                     universal.predicate.startswith("is_") and \
                     statement.predicate != universal.predicate:
                    # Only flag if the predicates are actually mutually exclusive
                    # Use the same logic as in LogicalStatement.contradicts()
                    stmt_base = statement.predicate[3:]
                    univ_base = universal.predicate[3:]

                    # Check for is_not_X vs is_X pattern
                    is_exclusive = False
                    if stmt_base.startswith("not_") and univ_base == stmt_base[4:]:
                        is_exclusive = True
                    elif univ_base.startswith("not_") and stmt_base == univ_base[4:]:
                        is_exclusive = True
                    else:
                        exclusive_categories = [
                            {'manager', 'engineer', 'developer', 'designer', 'analyst'},
                            {'active', 'inactive', 'suspended'},
                            {'on', 'off'},
                        ]

                        for category in exclusive_categories:
                            if stmt_base in category and univ_base in category:
                                is_exclusive = True
                                break

                    if is_exclusive:
                        violations.append(
                            f"Conflicts with universal rule: '{universal.raw_text}'"
                        )

        # Check conditional implications
        conditionals = self.memory.query(type=LogicalType.CONDITIONAL)
        for conditional in conditionals:
            # If the ground fact matches the condition, check the consequence
            if statement.subject == conditional.subject:
                # This is simplified - real implementation would be more sophisticated
                expected_consequent = conditional.object
                if expected_consequent and statement.predicate.startswith("not_"):
                    violations.append(
                        f"May violate conditional: '{conditional.raw_text}'"
                    )

        return violations

    def _check_conditional_chains(self, statement: LogicalStatement) -> List[str]:
        """Check if conditional statement creates logical chains

        Args:
            statement: A conditional statement to check

        Returns:
            List of violation messages
        """
        violations = []

        # Check for contradictory conditionals
        conditionals = self.memory.query(type=LogicalType.CONDITIONAL)
        for existing in conditionals:
            # Check if same antecedent leads to contradictory consequents
            if statement.subject == existing.subject:
                if statement.object and existing.object:
                    # Simple negation check
                    if statement.object.startswith("not_") and \
                       existing.object == statement.object[4:]:
                        violations.append(
                            f"Contradictory conditional: '{existing.raw_text}'"
                        )
                    elif existing.object.startswith("not_") and \
                         statement.object == existing.object[4:]:
                        violations.append(
                            f"Contradictory conditional: '{existing.raw_text}'"
                        )

        return violations

    def suggest_alternative(self, statement: LogicalStatement,
                           violations: List[str]) -> Optional[str]:
        """Suggest alternative phrasing that would be consistent

        Args:
            statement: The statement that has violations
            violations: List of violations found

        Returns:
            A suggestion string, or None if no suggestion available
        """
        if not violations:
            return None

        # Analyze violation types and provide suggestions
        if any("universal rule" in v.lower() for v in violations):
            return (f"According to stored rules, {statement.subject} should "
                   f"have different properties. Consider rephrasing or updating "
                   f"the universal rule.")

        if any("contradicts" in v.lower() for v in violations):
            return (f"This contradicts previously stated information about "
                   f"{statement.subject}. Consider using qualifiers like "
                   f"'sometimes' or 'usually' to express exceptions.")

        if any("conditional" in v.lower() for v in violations):
            return (f"This creates a logical conflict with existing conditional "
                   f"rules. Review the conditions and consequences.")

        return "This statement appears to conflict with previously established facts."

    def get_supporting_facts(self, statement: LogicalStatement) -> List[LogicalStatement]:
        """Get facts that support or relate to the given statement

        Args:
            statement: The statement to find support for

        Returns:
            List of related statements
        """
        related = []

        # Get statements with same subject
        related.extend(self.memory.query(subject=statement.subject))

        # For ground facts, get relevant universal rules
        if statement.type == LogicalType.GROUND:
            universals = self.memory.query(type=LogicalType.UNIVERSAL)
            for universal in universals:
                if self.memory._is_instance_of(statement.subject, universal.subject):
                    related.append(universal)

        return related

    def verify_knowledge_base(self) -> Tuple[bool, List[str]]:
        """Verify the entire knowledge base for internal consistency

        Returns:
            Tuple of (is_consistent, list of inconsistencies found)
        """
        inconsistencies = []

        # Check all ground facts against universal rules
        ground_facts = self.memory.query(type=LogicalType.GROUND)
        for fact in ground_facts:
            _, _, violations = self.check_consistency(fact)
            if violations:
                inconsistencies.append(
                    f"Fact '{fact.raw_text}' has violations: {', '.join(violations)}"
                )

        # Check for contradictory universals
        universals = self.memory.query(type=LogicalType.UNIVERSAL)
        for i, universal1 in enumerate(universals):
            for universal2 in universals[i+1:]:
                if universal1.contradicts(universal2):
                    inconsistencies.append(
                        f"Universal rules contradict: '{universal1.raw_text}' vs '{universal2.raw_text}'"
                    )

        is_consistent = len(inconsistencies) == 0
        return is_consistent, inconsistencies
