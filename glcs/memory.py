"""
Simple dictionary-based memory store for logical statements.
"""

from typing import Dict, List, Optional
from collections import defaultdict
from glcs.core import LogicalStatement, LogicalType
import json
import os


class SimpleMemory:
    """Simple dictionary-based memory store

    This memory store organizes logical statements by type and maintains
    an index for fast lookup by subject. It supports persistence to disk
    for maintaining state across sessions.
    """

    def __init__(self, persist_path: Optional[str] = "glcs_memory.json"):
        """Initialize the memory store

        Args:
            persist_path: Path to JSON file for persistence. None to disable persistence.
        """
        self.persist_path = persist_path

        # Separate storage for each logical type
        self.memory: Dict[LogicalType, List[LogicalStatement]] = {
            LogicalType.UNIVERSAL: [],
            LogicalType.CONDITIONAL: [],
            LogicalType.GROUND: []
        }

        # Index for fast lookup by subject
        self.subject_index: Dict[str, List[LogicalStatement]] = defaultdict(list)

        # Load from disk if file exists
        self.load()

    def store(self, statement: LogicalStatement) -> bool:
        """Store a logical statement

        Args:
            statement: The statement to store

        Returns:
            True if stored successfully, False if contradictions were found
        """
        # Check for contradictions first
        conflicts = self.find_conflicts(statement)
        if conflicts:
            return False  # Don't store contradictory statements

        # Store in appropriate level
        self.memory[statement.type].append(statement)

        # Update index
        self.subject_index[statement.subject].append(statement)

        # Persist to disk
        self.save()
        return True

    def find_conflicts(self, statement: LogicalStatement) -> List[LogicalStatement]:
        """Find statements that conflict with the given one

        Args:
            statement: The statement to check for conflicts

        Returns:
            List of conflicting statements
        """
        conflicts = []

        # Get all statements about the same subject
        related = self.subject_index.get(statement.subject, [])

        for existing in related:
            if statement.contradicts(existing):
                conflicts.append(existing)

        # Check universal rules if this is a ground fact
        if statement.type == LogicalType.GROUND:
            for universal in self.memory[LogicalType.UNIVERSAL]:
                # Check if ground fact violates universal
                if self._violates_universal(statement, universal):
                    conflicts.append(universal)

        return conflicts

    def _violates_universal(self, ground: LogicalStatement,
                           universal: LogicalStatement) -> bool:
        """Check if ground fact violates universal rule

        Args:
            ground: A ground fact statement
            universal: A universal rule statement

        Returns:
            True if the ground fact violates the universal rule
        """
        # Check if ground subject is an instance of universal subject
        # This is simplified - real implementation would need ontology
        if self._is_instance_of(ground.subject, universal.subject):
            # Check if predicates conflict
            if ground.predicate.startswith("not_") and universal.predicate == ground.predicate[4:]:
                return True
            if universal.predicate.startswith("not_") and ground.predicate == universal.predicate[4:]:
                return True
            # Check for mutually exclusive predicates
            if ground.predicate.startswith("is_") and universal.predicate.startswith("is_"):
                if ground.predicate != universal.predicate:
                    # Only flag if predicates are in same mutually exclusive category
                    ground_base = ground.predicate[3:]
                    univ_base = universal.predicate[3:]

                    # Check for is_not_X vs is_X pattern
                    if ground_base.startswith("not_") and univ_base == ground_base[4:]:
                        return True
                    if univ_base.startswith("not_") and ground_base == univ_base[4:]:
                        return True

                    exclusive_categories = [
                        {'manager', 'engineer', 'developer', 'designer', 'analyst'},
                        {'active', 'inactive', 'suspended'},
                        {'on', 'off'},
                    ]

                    for category in exclusive_categories:
                        if ground_base in category and univ_base in category:
                            return True

        return False

    def _is_instance_of(self, instance: str, category: str) -> bool:
        """Check if instance belongs to category (simplified)

        This is a simplified implementation. A production system would use
        a proper ontology or knowledge graph.

        Args:
            instance: The instance name (e.g., "penguin")
            category: The category name (e.g., "birds")

        Returns:
            True if instance is part of the category
        """
        # Simple mappings - in production, use a proper ontology
        mappings = {
            'birds': ['sparrow', 'penguin', 'eagle', 'robin', 'owl', 'parrot'],
            'employees': ['john', 'mary', 'bob', 'alice', 'charlie'],
            'servers': ['server1', 'server2', 'mainserver', 'backupserver'],
            'mammals': ['dog', 'cat', 'whale', 'dolphin', 'human'],
            'fish': ['salmon', 'tuna', 'goldfish'],
        }

        # Check direct membership
        if instance.lower() in mappings.get(category.lower(), []):
            return True

        # Check if instance is a singular form of category
        if category.endswith('s') and instance.lower() == category[:-1].lower():
            return True

        return False

    def query(self, subject: Optional[str] = None,
              type: Optional[LogicalType] = None) -> List[LogicalStatement]:
        """Query memory for relevant statements

        Args:
            subject: Filter by subject (optional)
            type: Filter by logical type (optional)

        Returns:
            List of matching statements
        """
        results = []

        if subject and type:
            # Filter by both subject and type
            results = [s for s in self.subject_index.get(subject, [])
                      if s.type == type]
        elif subject:
            # Filter by subject only
            results.extend(self.subject_index.get(subject, []))
        elif type:
            # Filter by type only
            results.extend(self.memory[type])
        else:
            # Return all statements
            for statements in self.memory.values():
                results.extend(statements)

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for stmt in results:
            key = f"{stmt.type.value}:{stmt.subject}:{stmt.predicate}:{stmt.object}"
            if key not in seen:
                seen.add(key)
                unique.append(stmt)

        return unique

    def save(self):
        """Persist memory to disk"""
        if self.persist_path:
            data = {
                'universal': [self._stmt_to_dict(s) for s in self.memory[LogicalType.UNIVERSAL]],
                'conditional': [self._stmt_to_dict(s) for s in self.memory[LogicalType.CONDITIONAL]],
                'ground': [self._stmt_to_dict(s) for s in self.memory[LogicalType.GROUND]]
            }
            with open(self.persist_path, 'w') as f:
                json.dump(data, f, indent=2)

    def load(self):
        """Load memory from disk"""
        if self.persist_path and os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, 'r') as f:
                    data = json.load(f)

                # Reconstruct statements
                for type_name, stmts in data.items():
                    type_enum = LogicalType(type_name)
                    for stmt_dict in stmts:
                        stmt = self._dict_to_stmt(stmt_dict)
                        self.memory[type_enum].append(stmt)
                        self.subject_index[stmt.subject].append(stmt)
            except (json.JSONDecodeError, KeyError) as e:
                # If loading fails, start with empty memory
                print(f"Warning: Could not load memory from {self.persist_path}: {e}")

    def _stmt_to_dict(self, stmt: LogicalStatement) -> dict:
        """Convert statement to dictionary

        Args:
            stmt: Statement to convert

        Returns:
            Dictionary representation
        """
        return {
            'type': stmt.type.value,
            'subject': stmt.subject,
            'predicate': stmt.predicate,
            'object': stmt.object,
            'confidence': stmt.confidence,
            'raw_text': stmt.raw_text,
            'metadata': stmt.metadata
        }

    def _dict_to_stmt(self, d: dict) -> LogicalStatement:
        """Convert dictionary to statement

        Args:
            d: Dictionary to convert

        Returns:
            LogicalStatement object
        """
        return LogicalStatement(
            type=LogicalType(d['type']),
            subject=d['subject'],
            predicate=d['predicate'],
            object=d.get('object'),
            confidence=d['confidence'],
            raw_text=d['raw_text'],
            metadata=d.get('metadata', {})
        )

    def clear(self):
        """Clear all memory"""
        self.memory = {
            LogicalType.UNIVERSAL: [],
            LogicalType.CONDITIONAL: [],
            LogicalType.GROUND: []
        }
        self.subject_index.clear()
        self.save()

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about stored statements

        Returns:
            Dictionary with counts for each statement type
        """
        return {
            'universal': len(self.memory[LogicalType.UNIVERSAL]),
            'conditional': len(self.memory[LogicalType.CONDITIONAL]),
            'ground': len(self.memory[LogicalType.GROUND]),
            'total': sum(len(stmts) for stmts in self.memory.values())
        }
