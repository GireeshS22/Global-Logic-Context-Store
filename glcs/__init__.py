"""
GLCS: Global Logical Context Store
A practical tool for detecting logical contradictions in LLM conversations.
"""

# Simple implementation (Stage 1.4) - import from modules directly
from glcs.parser import SimpleParser, LogicalStatement, LogicalType
from glcs.memory import SimpleMemory
from glcs.checker import ConsistencyChecker
from glcs.llm_wrapper import GLCSWrapper

# Advanced implementation (Stage 1.5) - available via glcs.core and glcs.advanced_wrapper
# from glcs.core import LLMLogicalParser, LogicalForm, SemanticEncoder, MemoryManager
# from glcs.advanced_wrapper import AdvancedGLCS

__version__ = "0.1.0"

__all__ = [
    "LogicalStatement",
    "LogicalType",
    "SimpleParser",
    "SimpleMemory",
    "ConsistencyChecker",
    "GLCSWrapper",
]
