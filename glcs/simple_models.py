"""
Core data structures for GLCS logical reasoning system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any


class LogicalType(Enum):
    """Types of logical statements supported by GLCS"""
    UNIVERSAL = "universal"      # All X are Y
    CONDITIONAL = "conditional"  # If X then Y
    GROUND = "ground"           # John is X


@dataclass
class LogicalStatement:
    """Represents a parsed logical statement

    Attributes:
        type: The type of logical statement (universal, conditional, or ground)
        subject: The subject of the statement
        predicate: The predicate describing the subject
        object: Optional object for conditional statements
        confidence: Confidence score (0-1) for this statement
        raw_text: Original text that was parsed
        metadata: Additional metadata about the statement
    """
    type: LogicalType
    subject: str
    predicate: str
    object: Optional[str] = None
    confidence: float = 0.9
    raw_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def contradicts(self, other: 'LogicalStatement') -> bool:
        """Check if this statement contradicts another statement

        Args:
            other: Another logical statement to check against

        Returns:
            True if the statements contradict each other, False otherwise
        """
        # Same subject check
        if self.subject != other.subject:
            return False

        # Check for negation contradictions
        if self.predicate.startswith("not_") and other.predicate == self.predicate[4:]:
            return True
        if other.predicate.startswith("not_") and self.predicate == other.predicate[4:]:
            return True

        # Check for mutually exclusive predicates (both start with "is_" but different)
        # Only flag as contradictory if they represent contradictory states
        # For example: is_manager vs is_engineer, but not is_employee vs is_benefits
        if self.predicate.startswith("is_") and other.predicate.startswith("is_"):
            # Extract the base predicate (without "is_")
            self_base = self.predicate[3:]
            other_base = other.predicate[3:]

            # Check for is_not_X vs is_X pattern
            if self_base.startswith("not_") and other_base == self_base[4:]:
                return True
            if other_base.startswith("not_") and self_base == other_base[4:]:
                return True

            # List of mutually exclusive role/state categories
            # In a real system, this would use a proper ontology
            exclusive_categories = [
                {'manager', 'engineer', 'developer', 'designer', 'analyst'},  # Job roles
                {'active', 'inactive', 'suspended'},  # Status states
                {'on', 'off'},  # Binary states
            ]

            # Check if both predicates are in the same exclusive category
            for category in exclusive_categories:
                if self_base in category and other_base in category:
                    return True

        return False

    def __str__(self) -> str:
        """String representation of the statement"""
        if self.object:
            return f"{self.type.value}: {self.subject} {self.predicate} {self.object}"
        return f"{self.type.value}: {self.subject} {self.predicate}"

    def __repr__(self) -> str:
        """Detailed representation for debugging"""
        return f"LogicalStatement(type={self.type}, subject='{self.subject}', predicate='{self.predicate}', object={self.object}, confidence={self.confidence})"
