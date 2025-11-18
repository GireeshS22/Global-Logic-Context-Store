"""
Simple rule-based parser for extracting logical statements from text.
"""

import re
from typing import Optional, List
from glcs.simple_models import LogicalStatement, LogicalType


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
                # Basic universal patterns
                r'all (\w+) (?:are|have|can) (\w+)',
                r'every (\w+) (?:is|has|can) (\w+)',
                r'no (\w+) (?:are|have|can) (\w+)',  # Negative universal
                r'(\w+) are always (\w+)',
                r'(\w+) can never (\w+)',
                # Enhanced universal patterns
                r'everyone (?:is|has|can) (\w+)',           # "everyone is welcome"
                r'nobody (?:is|has|can) (\w+)',             # "nobody is perfect"
                r'nothing (?:is|can) (\w+)',                # "nothing is impossible"
                r'everything (?:is|has) (\w+)',             # "everything is permitted"
                r'none of (?:the )?(\w+) (?:are|can) (\w+)', # "none of the users can access"
                r'only (\w+) (?:can|may) (\w+)',            # "only admins can delete"
            ],
            'conditional': [
                # Basic conditional patterns
                r'if (?:a |an |the )?(\w+) .* then .* (\w+)',
                r'when (?:a |an |the )?(\w+) .* (?:it |they |you )?(\w+)',
                r'whenever (\w+) .* (\w+)',
                # Enhanced natural language patterns
                r'if (?:it |the |a )?(\w+).*?(?:I will|I\'ll|you will|we will|will) (\w+)',
                r'if .*?(\w+)s .*?(?:I will|I\'ll|will) (\w+)',
                # New conditional patterns
                r'unless (\w+) .* (\w+)',                   # "unless alarm rings wake"
                r'either (\w+) or (\w+)',                   # "either succeed or fail"
                r'neither (\w+) nor (\w+)',                 # "neither hot nor cold"
                r'as long as (\w+) .* (\w+)',               # "as long as pays can stay"
            ],
            'ground': [
                # Basic ground fact patterns
                r'(\w+) is (?:a |an |the )?(\w+)',
                r'(\w+) has (?:a |an |the )?(\w+)',
                r'(\w+) can (\w+)',
                r'(\w+) cannot (\w+)',
                # Enhanced ground fact patterns
                r'(\w+) does not (\w+)',                    # "John does not code"
                r'(\w+) will (\w+)',                        # "Alice will attend"
                r'(\w+) won\'t (\w+)',                      # "Bob won't participate"
                r'(\w+) must (\w+)',                        # "Mary must approve"
                r'(\w+) should (\w+)',                      # "Charlie should review"
                r'(\w+) may (\w+)',                         # "Dave may join"
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
                # Handle patterns with 1 or 2 capture groups
                groups = match.groups()
                if len(groups) == 1:
                    # Patterns like "everyone is welcome" - only one capture group
                    if text_lower.startswith('everyone'):
                        subject = 'everyone'
                        predicate = groups[0]
                    elif text_lower.startswith('nobody'):
                        subject = 'nobody'
                        predicate = f"not_{groups[0]}"
                    elif text_lower.startswith('nothing'):
                        subject = 'nothing'
                        predicate = f"not_{groups[0]}"
                    elif text_lower.startswith('everything'):
                        subject = 'everything'
                        predicate = groups[0]
                    else:
                        subject = groups[0]
                        predicate = 'exists'
                else:
                    # Normal patterns with 2 capture groups
                    subject = groups[0]
                    predicate = groups[1]

                # Handle negation patterns
                if text_lower.startswith('no ') or 'never' in text_lower or text_lower.startswith('nobody'):
                    if not predicate.startswith('not_'):
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
