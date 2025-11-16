# GLCS Core Module

The `core` module contains the fundamental components that power GLCS's logical consistency checking system.

## Components

### 1. Data Models (`models.py`)

**Purpose**: Define all data structures used throughout the system

**Key Models**:
- `Entity` - Represents subjects/objects in logical statements
- `Relation` - Represents predicates/relations
- `LogicalType` - Enum for statement types (Universal, Existential, Conditional, Ground)
- `Polarity` - Enum for statement polarity (positive, negative)
- `LogicalForm` - Structured representation of parsed statements
- `Violation` - Represents detected contradictions
- `ConsistencyReport` - Return type for consistency checks

**Status**: ✅ Defined (Stage 0.3)

---

### 2. Logical Parser (`logical_parser.py`)

**Purpose**: Convert natural language text to structured `LogicalForm` objects

**Approach**:
- MVP: LLM-as-Parser (uses GPT-4 with structured output)
- Future: Fine-tuned smaller model

**Key Operations**:
- `parse(text, context_id)` → `LogicalForm`
- Handles retry logic for API failures
- Caching to reduce API calls

**Status**: ⏳ Coming in Stage 1.4

---

### 3. Semantic Encoder (`semantic_encoder.py`)

**Purpose**: Convert `LogicalForm` objects to vector embeddings

**Approach**:
- Uses sentence-transformers (all-MiniLM-L6-v2)
- Generates 384-dimensional vectors
- L2-normalized for cosine similarity

**Key Operations**:
- `encode(logical_form)` → `(vector, metadata)`
- `encode_batch(logical_forms)` → `List[(vector, metadata)]`

**Status**: ✅ Implemented (Stage 1.1)

---

### 4. Memory Manager (`memory_manager.py`)

**Purpose**: Store and retrieve logical statements

**Approach**:
- MVP: Naive linear search (simple lists)
- Future: FAISS-indexed vector store

**Key Operations**:
- `write(vector, logical_form, metadata)` → index
- `query(vector, k, level_filter)` → List[results]
- `get_stats()` → memory statistics
- `clear()` → reset memory

**Status**: ✅ Implemented (Stage 1.2)

---

### 5. Consistency Checker (`consistency_checker.py`)

**Purpose**: Validate logical consistency of new statements

**Algorithms**:
- **Direct Contradiction**: Same subject + predicate, opposite polarity
- **Hierarchical Validation** (Phase 2): Ground facts vs Universal rules
- **Transitive Reasoning** (Phase 4): Multi-hop inference

**Key Operations**:
- `check(logical_form, vector)` → `ConsistencyReport`

**Status**: ⏳ Coming in Stage 1.3

---

## Data Flow

```
Text Input
    ↓
[Logical Parser] → LogicalForm
    ↓
[Semantic Encoder] → (Vector, Metadata)
    ↓
[Memory Manager] ← Query for similar statements
    ↓
[Consistency Checker] → Check for contradictions
    ↓
ConsistencyReport (is_consistent, violations)
    ↓
If consistent: Write to Memory
```

## Design Principles

1. **Modularity**: Each component is independent and testable
2. **Pluggable**: Parser and encoder can be swapped without affecting other components
3. **Type-Safe**: Pydantic models ensure data validation
4. **Configurable**: All parameters controlled via `config/glcs_config.yaml`

## Usage Example

```python
from glcs.core.models import LogicalForm, Entity, Relation, LogicalType, Polarity
from glcs.core.semantic_encoder import SemanticEncoder
from glcs.core.memory_manager import MemoryManager
from glcs.core.consistency_checker import ConsistencyChecker

# Create a logical form
form = LogicalForm(
    context_id="test-123",
    original_text="All employees work remotely",
    logical_type=LogicalType.UNIVERSAL_RULE,
    subject=Entity(text="employees", entity_id="e1"),
    predicate=Relation(text="work_remotely", relation_id="r1"),
    polarity=Polarity.POSITIVE
)

# Encode it
encoder = SemanticEncoder()
vector, metadata = encoder.encode(form)

# Store in memory
memory = MemoryManager()
memory.write(vector, form, metadata)

# Check consistency of new statement
checker = ConsistencyChecker(memory)
report = checker.check(new_form, new_vector)

if not report.is_consistent:
    print(f"Violation detected: {report.violations[0].explanation}")
```

## Testing

Each component has corresponding unit tests in `tests/unit/`:
- `test_models.py`
- `test_semantic_encoder.py`
- `test_memory_manager.py`
- `test_consistency_checker.py`
- `test_logical_parser.py`

Run tests:
```bash
poetry run pytest tests/unit/test_*.py
```

## Dependencies

**Core Dependencies**:
- `pydantic` - Data validation and models
- `numpy` - Vector operations
- `sentence-transformers` - Embedding generation

**Optional Future**:
- `faiss-cpu` - Fast similarity search
- `openai` - LLM API for parsing

## Extension Points

To extend the core module:

1. **Add new LogicalType**: Update `LogicalType` enum in `models.py`
2. **Change embedding model**: Update `encoder.model_name` in config
3. **Optimize memory**: Replace naive search with FAISS in `memory_manager.py`
4. **Add new consistency algorithms**: Extend `ConsistencyChecker` methods

---

**Last Updated**: Stage 0.1 (Project Structure Setup)
