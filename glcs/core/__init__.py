"""
GLCS Core Module - Advanced PhD Implementation

This module contains the core components for the GLCS research implementation:
- Data models (LogicalForm, Entity, Relation, etc.)
- Semantic encoder (768-dimensional embeddings)
- Memory manager (ChromaDB vector database)
- Consistency checker (advanced contradiction detection)
- LLM-based logical parser (Stage 1.5)

Imports are lazy (#34): importing `glcs.core` does NOT eagerly load
sentence-transformers, ChromaDB, or LLM libraries.  Each heavy dependency
is only pulled in when you first access the corresponding name.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Only for type-checkers — never executed at runtime
    from glcs.core.models import (
        Entity, Relation, LogicalType, Polarity,
        ViolationType, Severity,
        LogicalForm, Violation, ConsistencyReport, BatchResult
    )
    from glcs.core.semantic_encoder import SemanticEncoder
    from glcs.core.memory_manager import MemoryManager
    from glcs.core.consistency_checker import ConsistencyChecker
    from glcs.core.logical_parser import LLMLogicalParser


_MODEL_NAMES = frozenset({
    'Entity', 'Relation', 'LogicalType', 'Polarity',
    'ViolationType', 'Severity',
    'LogicalForm', 'Violation', 'ConsistencyReport', 'BatchResult',
})

_COMPONENT_MAP = {
    'SemanticEncoder': 'glcs.core.semantic_encoder',
    'MemoryManager':   'glcs.core.memory_manager',
    'ConsistencyChecker': 'glcs.core.consistency_checker',
    'LLMLogicalParser': 'glcs.core.logical_parser',
}


def __getattr__(name: str):
    """Lazy attribute loader — defers heavy imports until first use."""
    if name in _MODEL_NAMES:
        import importlib
        mod = importlib.import_module('glcs.core.models')
        # Cache all model names at once so subsequent accesses are O(1)
        for attr in _MODEL_NAMES:
            globals()[attr] = getattr(mod, attr)
        return globals()[name]

    if name in _COMPONENT_MAP:
        import importlib
        mod = importlib.import_module(_COMPONENT_MAP[name])
        obj = getattr(mod, name)
        globals()[name] = obj
        return obj

    raise AttributeError(f"module 'glcs.core' has no attribute {name!r}")


__all__ = [
    # Data Models
    'Entity',
    'Relation',
    'LogicalType',
    'Polarity',
    'ViolationType',
    'Severity',
    'LogicalForm',
    'Violation',
    'ConsistencyReport',
    'BatchResult',
    # Core Components
    'SemanticEncoder',
    'MemoryManager',
    'ConsistencyChecker',
    'LLMLogicalParser',
]
