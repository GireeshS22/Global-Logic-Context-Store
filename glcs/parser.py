"""
Simple rule-based parser for extracting logical statements from text.
"""

import re
from typing import Optional, List
from glcs.core import LogicalStatement, LogicalType


class SimpleParser:
    """Rule-based parser for common logical patterns

    This parser uses regex patterns to identify and extract logical statements
    from natural language text. It supports three types of statements:
    - Universal: "All X are Y", "Every X is Y", "No X are Y"
    - Conditional: "If X then Y", "When X, Y"
    - Ground: "John is X", "Mary has Y"
    """

    def __init__(self):
        # Patterns for different logical types
        self.patterns = {
            'universal': [
                r'all (\w+) (?:are|have|can) (\w+)',
                r'every (\w+) (?:is|has|can) (\w+)',
                r'no (\w+) (?:are|have|can) (\w+)',  # Negative universal
                r'(\w+) are always (\w+)',
                r'(\w+) can never (\w+)',
            ],
            'conditional': [
                r'if (?:a |an |the )?(\w+) .* then .* (\w+)',
                r'when (?:a |an |the )?(\w+) .* (?:it |they |you )?(\w+)',
                r'whenever (\w+) .* (\w+)',
            ],
            'ground': [
                r'(\w+) is (?:a |an |the )?(\w+)',
                r'(\w+) has (?:a |an |the )?(\w+)',
                r'(\w+) can (\w+)',
                r'(\w+) cannot (\w+)',
            ]
        }

    def parse(self, text: str) -> Optional[LogicalStatement]:
        """Parse text into a logical statement

        Args:
            text: The text to parse

        Returns:
            A LogicalStatement if a pattern matches, None otherwise
        """
        text_lower = text.lower().strip()

        # Check universal patterns
        for pattern in self.patterns['universal']:
            match = re.search(pattern, text_lower)
            if match:
                subject = match.group(1)
                predicate = match.group(2)

                # Handle negation patterns
                if text_lower.startswith('no ') or 'never' in text_lower:
                    predicate = f"not_{predicate}"

                return LogicalStatement(
                    type=LogicalType.UNIVERSAL,
                    subject=subject,
                    predicate=f"is_{predicate}",
                    confidence=0.9,
                    raw_text=text
                )

        # Check conditional patterns
        for pattern in self.patterns['conditional']:
            match = re.search(pattern, text_lower)
            if match:
                return LogicalStatement(
                    type=LogicalType.CONDITIONAL,
                    subject=match.group(1),
                    predicate="implies",
                    object=match.group(2),
                    confidence=0.85,
                    raw_text=text
                )

        # Check ground fact patterns
        for pattern in self.patterns['ground']:
            match = re.search(pattern, text_lower)
            if match:
                subject = match.group(1)
                predicate = match.group(2)

                # Handle negation for ground facts
                if 'cannot' in text_lower or 'not' in text_lower:
                    predicate = f"not_{predicate}"

                return LogicalStatement(
                    type=LogicalType.GROUND,
                    subject=subject,
                    predicate=f"is_{predicate}",
                    confidence=0.95,
                    raw_text=text
                )

        return None

    def extract_statements(self, text: str) -> List[LogicalStatement]:
        """Extract all logical statements from text

        Args:
            text: The text to extract statements from

        Returns:
            A list of LogicalStatement objects found in the text
        """
        statements = []

        # Split by sentences (periods, exclamation marks, question marks)
        sentences = re.split(r'[.!?]+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                stmt = self.parse(sentence)
                if stmt:
                    statements.append(stmt)

        return statements

    def add_pattern(self, logical_type: str, pattern: str):
        """Add a custom pattern for parsing

        Args:
            logical_type: One of 'universal', 'conditional', or 'ground'
            pattern: A regex pattern with appropriate capture groups
        """
        if logical_type in self.patterns:
            self.patterns[logical_type].append(pattern)
        else:
            raise ValueError(f"Unknown logical type: {logical_type}")
