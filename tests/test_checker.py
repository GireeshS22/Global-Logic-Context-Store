"""
Tests for the ConsistencyChecker component
"""

import pytest
import tempfile
import os
from glcs.checker import ConsistencyChecker
from glcs.memory import SimpleMemory
from glcs.simple_models import LogicalStatement, LogicalType


class TestConsistencyChecker:
    """Test cases for the ConsistencyChecker class"""

    def setup_method(self):
        """Set up test fixtures"""
        # Use a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.memory = SimpleMemory(persist_path=self.temp_file.name)
        self.checker = ConsistencyChecker(self.memory)

    def teardown_method(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_check_consistent_statement(self):
        """Test checking a consistent statement"""
        stmt = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_manager",
            raw_text="John is a manager"
        )

        is_consistent, confidence, violations = self.checker.check_consistency(stmt)
        assert is_consistent is True
        assert confidence > 0.8
        assert len(violations) == 0

    def test_check_contradictory_statement(self):
        """Test checking a contradictory statement"""
        # First store a fact
        stmt1 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_manager",
            raw_text="John is a manager"
        )
        self.memory.store(stmt1)

        # Try to check a contradictory fact
        stmt2 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_engineer",
            raw_text="John is an engineer"
        )

        is_consistent, confidence, violations = self.checker.check_consistency(stmt2)
        assert is_consistent is False
        assert len(violations) > 0

    def test_check_negation_violation(self):
        """Test detecting negation violations"""
        stmt1 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="bob",
            predicate="is_fly",
            raw_text="Bob can fly"
        )
        self.memory.store(stmt1)

        stmt2 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="bob",
            predicate="is_not_fly",
            raw_text="Bob cannot fly"
        )

        is_consistent, confidence, violations = self.checker.check_consistency(stmt2)
        assert is_consistent is False
        assert len(violations) > 0

    def test_check_universal_violation(self):
        """Test detecting violations of universal rules"""
        # Store a universal rule
        universal = LogicalStatement(
            type=LogicalType.UNIVERSAL,
            subject="birds",
            predicate="is_fly",
            raw_text="All birds can fly"
        )
        self.memory.store(universal)

        # Try to add a ground fact that violates it
        ground = LogicalStatement(
            type=LogicalType.GROUND,
            subject="penguin",
            predicate="is_not_fly",
            raw_text="Penguins cannot fly"
        )

        is_consistent, confidence, violations = self.checker.check_consistency(ground)
        assert is_consistent is False
        assert len(violations) > 0
        assert any("universal" in v.lower() for v in violations)

    def test_suggest_alternative(self):
        """Test suggesting alternatives for inconsistent statements"""
        stmt1 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_manager",
            raw_text="John is a manager"
        )
        self.memory.store(stmt1)

        stmt2 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_engineer",
            raw_text="John is an engineer"
        )

        is_consistent, confidence, violations = self.checker.check_consistency(stmt2)
        suggestion = self.checker.suggest_alternative(stmt2, violations)

        assert suggestion is not None
        assert len(suggestion) > 0

    def test_get_supporting_facts(self):
        """Test getting supporting facts for a statement"""
        stmt1 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_manager",
            raw_text="John is a manager"
        )
        stmt2 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_senior",
            raw_text="John is senior"
        )
        self.memory.store(stmt1)
        self.memory.store(stmt2)

        # Get supporting facts for a new statement about john
        new_stmt = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_experienced",
            raw_text="John is experienced"
        )

        supporting = self.checker.get_supporting_facts(new_stmt)
        # Should find at least one (the query returns facts about the same subject)
        assert len(supporting) >= 1

    def test_verify_knowledge_base_consistent(self):
        """Test verifying a consistent knowledge base"""
        stmt1 = LogicalStatement(
            type=LogicalType.UNIVERSAL,
            subject="birds",
            predicate="is_fly",
            raw_text="All birds can fly"
        )
        stmt2 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="sparrow",
            predicate="is_fly",
            raw_text="Sparrows can fly"
        )
        self.memory.store(stmt1)
        self.memory.store(stmt2)

        is_consistent, inconsistencies = self.checker.verify_knowledge_base()
        assert is_consistent is True
        assert len(inconsistencies) == 0

    def test_verify_knowledge_base_inconsistent(self):
        """Test verifying an inconsistent knowledge base"""
        # Manually add contradictory statements (bypassing consistency checks)
        stmt1 = LogicalStatement(
            type=LogicalType.UNIVERSAL,
            subject="birds",
            predicate="is_fly",
            raw_text="All birds can fly"
        )
        stmt2 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="penguin",
            predicate="is_not_fly",
            raw_text="Penguins cannot fly"
        )

        # Add directly to memory without check
        self.memory.memory[LogicalType.UNIVERSAL].append(stmt1)
        self.memory.memory[LogicalType.GROUND].append(stmt2)
        self.memory.subject_index["birds"].append(stmt1)
        self.memory.subject_index["penguin"].append(stmt2)

        is_consistent, inconsistencies = self.checker.verify_knowledge_base()
        assert is_consistent is False
        assert len(inconsistencies) > 0

    def test_confidence_decreases_with_violations(self):
        """Test that confidence decreases with more violations"""
        stmt1 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_manager",
            raw_text="John is a manager",
            confidence=0.9
        )
        self.memory.store(stmt1)

        stmt2 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_engineer",
            raw_text="John is an engineer",
            confidence=0.9
        )

        is_consistent, confidence, violations = self.checker.check_consistency(stmt2)
        assert confidence < stmt2.confidence

    def test_check_conditional_chains(self):
        """Test checking conditional statement chains"""
        cond1 = LogicalStatement(
            type=LogicalType.CONDITIONAL,
            subject="rain",
            predicate="implies",
            object="wet",
            raw_text="If it rains then it is wet"
        )
        self.memory.store(cond1)

        # Contradictory conditional
        cond2 = LogicalStatement(
            type=LogicalType.CONDITIONAL,
            subject="rain",
            predicate="implies",
            object="not_wet",
            raw_text="If it rains then it is not wet"
        )

        is_consistent, confidence, violations = self.checker.check_consistency(cond2)
        assert is_consistent is False
        assert len(violations) > 0
