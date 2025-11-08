"""
OpenAI API wrapper with GLCS consistency checking.
"""

import os
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv
from glcs.parser import SimpleParser
from glcs.memory import SimpleMemory
from glcs.checker import ConsistencyChecker
from glcs.core import LogicalStatement, LogicalType

# Load environment variables
load_dotenv()


class GLCSWrapper:
    """Wrapper for OpenAI API with GLCS consistency checking

    This wrapper integrates GLCS with OpenAI's API to provide
    consistency checking for both prompts and responses.
    """

    def __init__(self, api_key: Optional[str] = None,
                 memory_path: Optional[str] = None,
                 model: str = "gpt-3.5-turbo"):
        """Initialize the GLCS wrapper

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            memory_path: Path for memory persistence (defaults to glcs_memory.json)
            model: OpenAI model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        # Initialize OpenAI client (using new API)
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            )

        # Initialize GLCS components
        self.parser = SimpleParser()
        self.memory = SimpleMemory(
            persist_path=memory_path or os.getenv("GLCS_MEMORY_PATH", "glcs_memory.json")
        )
        self.checker = ConsistencyChecker(self.memory)

        # Conversation history
        self.history: List[Dict[str, str]] = []

    def check_and_store(self, text: str) -> Tuple[bool, List[str]]:
        """Check consistency and store if valid

        Args:
            text: Text to check and potentially store

        Returns:
            Tuple of (all_consistent, violations)
        """
        statements = self.parser.extract_statements(text)
        all_consistent = True
        all_violations = []

        for stmt in statements:
            is_consistent, confidence, violations = self.checker.check_consistency(stmt)

            if is_consistent:
                # Store the statement
                success = self.memory.store(stmt)
                if not success:
                    all_consistent = False
                    all_violations.append(f"Failed to store: {stmt.raw_text}")
            else:
                all_consistent = False
                all_violations.extend(violations)

        return all_consistent, all_violations

    def _build_context(self, max_facts: int = 10) -> str:
        """Build context from stored knowledge

        Args:
            max_facts: Maximum number of facts to include

        Returns:
            Formatted context string
        """
        context_parts = []

        # Get recent facts from memory
        stats = self.memory.get_stats()
        if stats['total'] > 0:
            context_parts.append("Known facts:")

            # Get some universal rules
            universals = self.memory.query(type=LogicalType.UNIVERSAL)
            for stmt in universals[:3]:  # Include up to 3 universal rules
                context_parts.append(f"- {stmt.raw_text}")

            # Get some ground facts
            grounds = self.memory.query(type=LogicalType.GROUND)
            for stmt in grounds[:max(0, max_facts - 3)]:
                context_parts.append(f"- {stmt.raw_text}")

        return "\n".join(context_parts) if context_parts else ""

    def generate(self, prompt: str,
                 check_consistency: bool = True,
                 max_tokens: int = 150,
                 temperature: float = 0.7) -> Dict[str, Any]:
        """Generate response with optional consistency checking

        Args:
            prompt: User prompt
            check_consistency: Whether to check consistency
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Dictionary with response and metadata
        """
        result = {
            'prompt': prompt,
            'response': '',
            'consistent': True,
            'violations': [],
            'stored_facts': 0
        }

        # Check prompt consistency
        if check_consistency:
            prompt_consistent, prompt_violations = self.check_and_store(prompt)
            result['consistent'] = prompt_consistent
            result['violations'].extend(prompt_violations)

        # Build context from memory
        context = self._build_context()

        # Augment prompt with context if available
        if context:
            augmented_prompt = f"{context}\n\nUser: {prompt}\n\nPlease respond while respecting the known facts above."
        else:
            augmented_prompt = prompt

        # Add to history
        self.history.append({"role": "user", "content": prompt})

        # Generate response
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Be logically consistent and respect established facts."},
                    *self.history[-10:],  # Include last 10 messages for context
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            response_text = response.choices[0].message.content
            result['response'] = response_text

            # Add to history
            self.history.append({"role": "assistant", "content": response_text})

            # Check response consistency
            if check_consistency:
                response_consistent, response_violations = self.check_and_store(response_text)

                # If response is inconsistent, note it but still return it
                if not response_consistent:
                    result['consistent'] = False
                    result['violations'].extend(response_violations)

                    # Optionally regenerate with constraints
                    # For now, we just flag the inconsistency

        except Exception as e:
            result['response'] = f"Error generating response: {str(e)}"
            result['consistent'] = False
            result['violations'].append(str(e))

        # Add statistics
        result['memory_stats'] = self.memory.get_stats()

        return result

    def verify_statement(self, statement: str) -> Dict[str, Any]:
        """Verify a statement against stored knowledge

        Args:
            statement: Statement to verify

        Returns:
            Dictionary with verification results
        """
        result = {
            'statement': statement,
            'parsed': False,
            'consistent': True,
            'confidence': 0.0,
            'violations': [],
            'supporting_facts': []
        }

        # Try to parse the statement
        parsed = self.parser.parse(statement)
        if not parsed:
            result['parsed'] = False
            result['violations'].append("Could not parse statement into logical form")
            return result

        result['parsed'] = True

        # Check consistency
        is_consistent, confidence, violations = self.checker.check_consistency(parsed)
        result['consistent'] = is_consistent
        result['confidence'] = confidence
        result['violations'] = violations

        # Get supporting facts
        supporting = self.checker.get_supporting_facts(parsed)
        result['supporting_facts'] = [s.raw_text for s in supporting]

        return result

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of stored knowledge

        Returns:
            Dictionary with memory statistics and samples
        """
        stats = self.memory.get_stats()

        summary = {
            'statistics': stats,
            'universal_rules': [],
            'conditionals': [],
            'ground_facts': []
        }

        # Get samples of each type
        universals = self.memory.query(type=LogicalType.UNIVERSAL)
        summary['universal_rules'] = [s.raw_text for s in universals[:5]]

        conditionals = self.memory.query(type=LogicalType.CONDITIONAL)
        summary['conditionals'] = [s.raw_text for s in conditionals[:5]]

        grounds = self.memory.query(type=LogicalType.GROUND)
        summary['ground_facts'] = [s.raw_text for s in grounds[:10]]

        return summary

    def clear_memory(self):
        """Clear all stored knowledge"""
        self.memory.clear()
        self.history.clear()

    def reset_conversation(self):
        """Reset conversation history but keep memory"""
        self.history.clear()

    def verify_knowledge_base(self) -> Dict[str, Any]:
        """Verify internal consistency of knowledge base

        Returns:
            Dictionary with verification results
        """
        is_consistent, inconsistencies = self.checker.verify_knowledge_base()

        return {
            'consistent': is_consistent,
            'inconsistencies': inconsistencies,
            'total_statements': self.memory.get_stats()['total']
        }
