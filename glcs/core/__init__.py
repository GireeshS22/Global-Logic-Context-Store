"""
GLCS Core Module - Advanced PhD Implementation

This module contains the core components for the GLCS research implementation:
- Data models (LogicalForm, Entity, Relation, etc.)
- Semantic encoder (768-dimensional embeddings)
- Memory manager (ChromaDB vector database)
- Consistency checker (advanced contradiction detection)
- LLM-based logical parser (Stage 1.5)
"""

from glcs.core.models import (
    Entity,
    Relation,
    LogicalType,
    Polarity,
    LogicalForm,
    Violation,
    ConsistencyReport,
)
from glcs.core.semantic_encoder import SemanticEncoder
from glcs.core.memory_manager import MemoryManager
from glcs.core.consistency_checker import ConsistencyChecker
from glcs.core.logical_parser import LLMLogicalParser

__all__ = [
    # Data Models
    'Entity',
    'Relation',
    'LogicalType',
    'Polarity',
    'LogicalForm',
    'Violation',
    'ConsistencyReport',
    # Core Components
    'SemanticEncoder',
    'MemoryManager',
    'ConsistencyChecker',
    'LLMLogicalParser',
]
