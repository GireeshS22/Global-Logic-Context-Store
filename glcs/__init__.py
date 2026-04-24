from __future__ import annotations
from typing import TYPE_CHECKING

# Simple implementation (Stage 1.4)
from glcs.simple_models import LogicalStatement, LogicalType as SimpleLogicalType
from glcs.parser import SimpleParser
from glcs.memory import SimpleMemory
from glcs.checker import SimpleConsistencyChecker
from glcs.llm_wrapper import GLCSWrapper

if TYPE_CHECKING:
    # Only for type-checkers — never executed at runtime
    # This provides IDE autocomplete without eager imports
    from glcs.advanced_wrapper import AdvancedGLCS
    from glcs.core import (
        LLMLogicalParser, LogicalForm, SemanticEncoder, MemoryManager,
        ConsistencyChecker, Entity, Relation, LogicalType, Polarity,
        ViolationType, Severity, Violation, ConsistencyReport, BatchResult
    )

__version__ = "0.1.0"

_ADVANCED_EXPORTS = {
    'AdvancedGLCS': 'glcs.advanced_wrapper',
    'LLMLogicalParser': 'glcs.core',
    'LogicalForm': 'glcs.core',
    'SemanticEncoder': 'glcs.core',
    'MemoryManager': 'glcs.core',
    'ConsistencyChecker': 'glcs.core',
    'Entity': 'glcs.core',
    'Relation': 'glcs.core',
    'LogicalType': 'glcs.core',
    'Polarity': 'glcs.core',
    'ViolationType': 'glcs.core',
    'Severity': 'glcs.core',
    'Violation': 'glcs.core',
    'ConsistencyReport': 'glcs.core',
    'BatchResult': 'glcs.core',
}

def __getattr__(name: str):
    """Lazy loader for advanced components."""
    if name in _ADVANCED_EXPORTS:
        import importlib
        module_path = _ADVANCED_EXPORTS[name]
        module = importlib.import_module(module_path)
        attr = getattr(module, name)
        # Cache for subsequent access
        globals()[name] = attr
        return attr
    raise AttributeError(f"module 'glcs' has no attribute {name!r}")

__all__ = [
    # Simple API (Stage 1.4)
    "LogicalStatement",
    "SimpleLogicalType",
    "SimpleParser",
    "SimpleMemory",
    "SimpleConsistencyChecker",
    "GLCSWrapper",
    
    # Advanced API (Stage 1.5)
    "AdvancedGLCS",
    "LLMLogicalParser",
    "LogicalForm",
    "SemanticEncoder",
    "MemoryManager",
    "ConsistencyChecker",
    "Entity",
    "Relation",
    "LogicalType",
    "Polarity",
    "ViolationType",
    "Severity",
    "Violation",
    "ConsistencyReport",
    "BatchResult",
]
