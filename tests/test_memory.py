"""
Tests for the SimpleMemory component
"""

import pytest
import os
import tempfile
from glcs.memory import SimpleMemory
from glcs.simple_models import LogicalStatement, LogicalType


class TestSimpleMemory:
    """Test cases for the SimpleMemory class"""

    def setup_method(self):
        """Set up test fixtures"""
        # Use a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.memory = SimpleMemory(persist_path=self.temp_file.name)

    def teardown_method(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_store_universal_statement(self):
        """Test storing a universal statement"""
        stmt = LogicalStatement(
            type=LogicalType.UNIVERSAL,
            subject="birds",
            predicate="is_fly",
            raw_text="All birds can fly"
        )
        result = self.memory.store(stmt)
        assert result is True
        assert len(self.memory.memory[LogicalType.UNIVERSAL]) == 1

    def test_store_ground_fact(self):
        """Test storing a ground fact"""
        stmt = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_manager",
            raw_text="John is a manager"
        )
        result = self.memory.store(stmt)
        assert result is True
        assert len(self.memory.memory[LogicalType.GROUND]) == 1

    def test_store_conditional(self):
        """Test storing a conditional statement"""
        stmt = LogicalStatement(
            type=LogicalType.CONDITIONAL,
            subject="server",
            predicate="implies",
            object="restarts",
            raw_text="If server crashes then it restarts"
        )
        result = self.memory.store(stmt)
        assert result is True
        assert len(self.memory.memory[LogicalType.CONDITIONAL]) == 1

    def test_find_direct_contradiction(self):
        """Test finding direct contradictions"""
        stmt1 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_manager",
            raw_text="John is a manager"
        )
        stmt2 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_engineer",
            raw_text="John is an engineer"
        )

        self.memory.store(stmt1)
        conflicts = self.memory.find_conflicts(stmt2)
        assert len(conflicts) > 0

    def test_find_negation_contradiction(self):
        """Test finding negation contradictions"""
        stmt1 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="bob",
            predicate="is_fly",
            raw_text="Bob can fly"
        )
        stmt2 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="bob",
            predicate="is_not_fly",
            raw_text="Bob cannot fly"
        )

        self.memory.store(stmt1)
        conflicts = self.memory.find_conflicts(stmt2)
        assert len(conflicts) == 1

    def test_query_by_subject(self):
        """Test querying statements by subject"""
        stmt1 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_manager",
            raw_text="John is a manager"
        )
        stmt2 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="mary",
            predicate="is_engineer",
            raw_text="Mary is an engineer"
        )

        self.memory.store(stmt1)
        self.memory.store(stmt2)

        results = self.memory.query(subject="john")
        assert len(results) == 1
        assert results[0].subject == "john"

    def test_query_by_type(self):
        """Test querying statements by type"""
        stmt1 = LogicalStatement(
            type=LogicalType.UNIVERSAL,
            subject="birds",
            predicate="is_fly",
            raw_text="All birds can fly"
        )
        stmt2 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_manager",
            raw_text="John is a manager"
        )

        self.memory.store(stmt1)
        self.memory.store(stmt2)

        results = self.memory.query(type=LogicalType.UNIVERSAL)
        assert len(results) == 1
        assert results[0].type == LogicalType.UNIVERSAL

    def test_persistence_save_load(self):
        """Test saving and loading from disk"""
        stmt = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_manager",
            raw_text="John is a manager"
        )
        self.memory.store(stmt)

        # Create new memory instance with same path
        new_memory = SimpleMemory(persist_path=self.temp_file.name)
        assert len(new_memory.memory[LogicalType.GROUND]) == 1
        assert new_memory.memory[LogicalType.GROUND][0].subject == "john"

    def test_clear_memory(self):
        """Test clearing all memory"""
        stmt = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_manager",
            raw_text="John is a manager"
        )
        self.memory.store(stmt)
        self.memory.clear()

        stats = self.memory.get_stats()
        assert stats['total'] == 0

    def test_get_stats(self):
        """Test getting memory statistics"""
        stmt1 = LogicalStatement(
            type=LogicalType.UNIVERSAL,
            subject="birds",
            predicate="is_fly",
            raw_text="All birds can fly"
        )
        stmt2 = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_manager",
            raw_text="John is a manager"
        )

        self.memory.store(stmt1)
        self.memory.store(stmt2)

        stats = self.memory.get_stats()
        assert stats['universal'] == 1
        assert stats['ground'] == 1
        assert stats['total'] == 2

    def test_subject_index_updated(self):
        """Test that subject index is properly maintained"""
        stmt = LogicalStatement(
            type=LogicalType.GROUND,
            subject="john",
            predicate="is_manager",
            raw_text="John is a manager"
        )
        self.memory.store(stmt)

        assert "john" in self.memory.subject_index
        assert len(self.memory.subject_index["john"]) == 1

    def test_is_instance_of(self):
        """Test instance checking"""
        assert self.memory._is_instance_of("penguin", "birds") is True
        assert self.memory._is_instance_of("john", "employees") is True
        assert self.memory._is_instance_of("cat", "birds") is False
