"""
GLCS: Global Logical Context Store
A practical tool for detecting logical contradictions in LLM conversations.
"""

from glcs.core import LogicalStatement, LogicalType
from glcs.parser import SimpleParser
from glcs.memory import SimpleMemory
from glcs.checker import ConsistencyChecker
from glcs.llm_wrapper import GLCSWrapper

__version__ = "0.1.0"

__all__ = [
    "LogicalStatement",
    "LogicalType",
    "SimpleParser",
    "SimpleMemory",
    "ConsistencyChecker",
    "GLCSWrapper",
]
