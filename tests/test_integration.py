"""
Integration tests for the complete GLCS system
"""

import pytest
import tempfile
import os
from glcs.parser import SimpleParser
from glcs.memory import SimpleMemory
from glcs.checker import ConsistencyChecker
from glcs.core import LogicalType, LogicalStatement


class TestIntegration:
    """Integration test cases for the complete GLCS system"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()

        self.parser = SimpleParser()
        self.memory = SimpleMemory(persist_path=self.temp_file.name)
        self.checker = ConsistencyChecker(self.memory)

    def teardown_method(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_parse_store_check_workflow(self):
        """Test the complete parse -> store -> check workflow"""
        # Parse a statement
        text = "All birds can fly"
        stmt = self.parser.parse(text)
        assert stmt is not None

        # Check and store it
        is_consistent, confidence, violations = self.checker.check_consistency(stmt)
        assert is_consistent is True

        result = self.memory.store(stmt)
        assert result is True

        # Parse and check a statement that contradicts if we know penguin is a bird
        # For our simple system, manually create the contradiction scenario
        text2 = "penguin cannot fly"
        stmt2 = self.parser.parse(text2)
        assert stmt2 is not None

        # The violation depends on the ontology recognizing penguin as a bird
        # Our simple system has penguin in the birds category
        is_consistent2, confidence2, violations2 = self.checker.check_consistency(stmt2)
        # Should detect contradiction since penguin is in our birds ontology
        assert is_consistent2 is False
        assert len(violations2) > 0

    def test_conversation_flow(self):
        """Test a realistic conversation flow with multiple turns"""
        conversation = [
            "All employees have benefits",
            "John is an employee",
            "Mary is an employee",
        ]

        for text in conversation:
            stmts = self.parser.extract_statements(text)
            for stmt in stmts:
                is_consistent, _, violations = self.checker.check_consistency(stmt)
                if is_consistent:
                    self.memory.store(stmt)

        # Check memory state
        stats = self.memory.get_stats()
        assert stats['total'] >= 3  # universal + 2 ground facts

    def test_contradiction_detection_scenario(self):
        """Test a classic contradiction scenario"""
        # Test direct ground fact contradiction
        facts = [
            "John is a manager",
            "John is an engineer",  # Contradiction!
        ]

        violations_found = False
        for text in facts:
            stmt = self.parser.parse(text)
            if stmt:
                is_consistent, _, violations = self.checker.check_consistency(stmt)
                if not is_consistent:
                    violations_found = True
                    break
                self.memory.store(stmt)

        # Should detect contradiction on the second statement
        assert violations_found is True

    def test_persistence_across_sessions(self):
        """Test that memory persists across sessions"""
        # First session
        stmt = self.parser.parse("John is a manager")
        self.memory.store(stmt)

        # Simulate new session
        new_memory = SimpleMemory(persist_path=self.temp_file.name)
        new_checker = ConsistencyChecker(new_memory)

        # Check that previous fact is still there
        stats = new_memory.get_stats()
        assert stats['total'] == 1

        # Try to add contradictory fact
        stmt2 = self.parser.parse("John is an engineer")
        is_consistent, _, _ = new_checker.check_consistency(stmt2)
        assert is_consistent is False

    def test_complex_reasoning_chain(self):
        """Test a more complex reasoning chain"""
        statements = [
            "All managers have teams",
            "John is a manager",
            # John should have a team (implied)
        ]

        for text in statements:
            stmt = self.parser.parse(text)
            if stmt:
                is_consistent, _, _ = self.checker.check_consistency(stmt)
                if is_consistent:
                    self.memory.store(stmt)

        # Check that both statements were stored
        stats = self.memory.get_stats()
        assert stats['universal'] >= 1
        assert stats['ground'] >= 1

    def test_multiple_contradictions(self):
        """Test handling multiple contradictions"""
        # Store initial facts
        self.memory.store(self.parser.parse("All birds can fly"))

        # Try statement about penguin which is in our ontology
        penguin = self.parser.parse("penguin cannot fly")
        penguin_check = self.checker.check_consistency(penguin)

        # Should detect violation since penguin is in birds category
        assert penguin_check[0] is False

    def test_conditional_reasoning(self):
        """Test conditional reasoning chains"""
        statements = [
            "If a server crashes then it restarts",
            "Server1 crashes",
            # Should imply Server1 restarts
        ]

        for text in statements:
            stmt = self.parser.parse(text)
            if stmt:
                is_consistent, _, _ = self.checker.check_consistency(stmt)
                if is_consistent:
                    self.memory.store(stmt)

        stats = self.memory.get_stats()
        assert stats['conditional'] >= 1

    def test_empty_memory_behavior(self):
        """Test behavior with empty memory"""
        stmt = self.parser.parse("John is a manager")
        is_consistent, confidence, violations = self.checker.check_consistency(stmt)

        # Should be consistent since there's nothing to contradict
        assert is_consistent is True
        assert len(violations) == 0
        assert confidence > 0.8

    def test_query_related_facts(self):
        """Test querying related facts after storing multiple statements"""
        statements = [
            "All birds can fly",
            "Sparrows are birds",
            "John has a sparrow",
        ]

        for text in statements:
            stmts = self.parser.extract_statements(text)
            for stmt in stmts:
                is_consistent, _, _ = self.checker.check_consistency(stmt)
                if is_consistent:
                    self.memory.store(stmt)

        # Query for bird-related facts
        bird_facts = self.memory.query(subject="birds")
        assert len(bird_facts) >= 1

        # Query for universals
        universals = self.memory.query(type=LogicalType.UNIVERSAL)
        assert len(universals) >= 1

    def test_suggest_alternatives_workflow(self):
        """Test the workflow of getting suggestions for contradictions"""
        # Store a fact
        stmt1 = self.parser.parse("John is a manager")
        self.memory.store(stmt1)

        # Try contradictory fact
        stmt2 = self.parser.parse("John is an engineer")
        is_consistent, _, violations = self.checker.check_consistency(stmt2)

        if not is_consistent:
            suggestion = self.checker.suggest_alternative(stmt2, violations)
            assert suggestion is not None
            assert len(suggestion) > 0

    def test_knowledge_base_verification(self):
        """Test verifying the entire knowledge base"""
        # Add consistent facts
        consistent_facts = [
            "All mammals breathe",
            "Dogs are mammals",
        ]

        for text in consistent_facts:
            stmt = self.parser.parse(text)
            if stmt:
                self.memory.store(stmt)

        is_consistent, inconsistencies = self.checker.verify_knowledge_base()
        assert is_consistent is True
        assert len(inconsistencies) == 0

    def test_edge_case_same_statement_twice(self):
        """Test storing the same statement twice"""
        text = "John is a manager"
        stmt1 = self.parser.parse(text)
        stmt2 = self.parser.parse(text)

        result1 = self.memory.store(stmt1)
        result2 = self.memory.store(stmt2)

        # Both should succeed (or implementation might prevent duplicates)
        assert result1 is True
        # Second one might fail or succeed depending on duplicate handling
        # For now, we just check it doesn't crash

    def test_case_insensitive_parsing(self):
        """Test that parsing is case-insensitive"""
        stmt1 = self.parser.parse("All BIRDS can FLY")
        stmt2 = self.parser.parse("all birds can fly")

        assert stmt1 is not None
        assert stmt2 is not None
        assert stmt1.subject == stmt2.subject
        assert stmt1.predicate == stmt2.predicate
