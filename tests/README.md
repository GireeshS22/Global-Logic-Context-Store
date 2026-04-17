# GLCS Testing Guide

This directory contains all tests for the GLCS project.

**Last Updated:** 2026-04-17
**Total unit tests collected:** 234

---

## Test Organisation

```
tests/
├── unit/                        # Unit tests for individual components
│   ├── test_models.py           # Data model validation (50 tests)
│   ├── test_config_manager.py   # Configuration loading (13 tests)
│   ├── test_logger.py           # Logging functionality (7 tests)
│   ├── test_exceptions.py       # Custom exception hierarchy (16 tests)
│   ├── test_semantic_encoder.py # Vector encoding (35 tests)
│   ├── test_memory_manager.py   # ChromaDB CRUD + round-trip (34 tests)
│   ├── test_consistency_checker.py  # Contradiction/redundancy logic (23 tests)
│   ├── test_llm_parser.py       # LLM logical parser (35 tests, mocked)
│   └── test_providers/
│       └── test_provider_system.py  # Provider factory + 5 providers (23 tests)
├── integration/
│   └── test_advanced_glcs.py    # End-to-end AdvancedGLCS workflows
├── api/
│   └── test_api.py              # REST API endpoint tests
├── fixtures/                    # Shared test data
└── README.md                    # This file
```

---

## Running Tests

### All unit tests

```bash
poetry run pytest tests/unit/ -q
```

### With verbose output

```bash
poetry run pytest tests/unit/ -v
```

### Stop on first failure

```bash
poetry run pytest tests/unit/ -x
```

### With coverage report

```bash
poetry run pytest tests/unit/ --cov=glcs --cov-report=term-missing
```

### Run a specific test file

```bash
poetry run pytest tests/unit/test_models.py
poetry run pytest tests/unit/test_memory_manager.py
poetry run pytest tests/unit/test_consistency_checker.py
```

### Run a specific test class or function

```bash
# Entire class
poetry run pytest tests/unit/test_models.py::TestLogicalForm

# Single test
poetry run pytest tests/unit/test_models.py::TestLogicalForm::test_logical_form_creation_valid_minimal

# By keyword
poetry run pytest -k "round_trip"
```

### Show print output during tests

```bash
poetry run pytest -s
```

### Drop into debugger on failure

```bash
poetry run pytest --pdb
```

### Re-run only last failed tests

```bash
poetry run pytest --lf
```

---

## Test Coverage Requirements

| Layer            | Minimum |
|------------------|---------|
| Core components  | 90%     |
| Utilities        | 85%     |
| API layer        | 75%     |
| Overall          | 80%     |

Check coverage:

```bash
poetry run pytest --cov=glcs --cov-report=html
# Open htmlcov/index.html in a browser
```

---

## Unit Test Files

### `test_models.py` — 50 tests

Tests all Pydantic data models.

**Classes covered:**
- `TestEntity` — name normalisation, metadata, UUID generation
- `TestRelation` — verb normalisation, relation_type
- `TestLogicalType` — enum completeness (4 values)
- `TestPolarity` — enum completeness (2 values)
- `TestViolationType` — enum completeness (4 values), invalid type rejection
- `TestSeverity` — enum completeness (3 values)
- `TestLogicalForm` — embedding validation, confidence range, serialisation round-trip
- `TestViolation` — severity enum, minimum conflicting forms
- `TestConsistencyReport` — `is_consistent` auto-computed from violations
- `TestIntegration` — full model workflow

**Key invariants tested:**
- `Entity.name` and `Relation.verb` are normalised to lowercase and stripped
- `LogicalForm.embedding` accepts any non-empty 1D numpy array (not hardcoded to 768)
- `Violation.violation_type` must be a `ViolationType` enum value
- `Violation.severity` must be a `Severity` enum value
- `ConsistencyReport.is_consistent` is a computed field — always derived from `violations`

**Example:**

```python
from glcs.core.models import (
    Entity, Relation, LogicalType, Polarity,
    ViolationType, Severity,
    LogicalForm, Violation, ConsistencyReport,
)
from uuid import uuid4

# Create a LogicalForm
form = LogicalForm(
    context_id="session-123",
    logical_type=LogicalType.UNIVERSAL_RULE,
    subject=Entity(name="humans", entity_type="species"),
    predicate=Relation(verb="are", relation_type="property"),
    object=Entity(name="mortal"),
    polarity=Polarity.POSITIVE,
    source_text="All humans are mortal",
    confidence_score=0.95,
)

# Create a Violation using typed enums
violation = Violation(
    violation_type=ViolationType.UNIVERSAL_GROUND_CONTRADICTION,
    conflicting_forms=[form.form_id, uuid4()],
    severity=Severity.HIGH,
    explanation="Universal rule contradicts ground fact",
)

# ConsistencyReport.is_consistent is auto-computed
report = ConsistencyReport(
    context_id="session-123",
    violations=[violation],
    total_forms_checked=5,
)
assert report.is_consistent is False  # auto-derived from violations
```

---

### `test_memory_manager.py` — 34 tests

Tests ChromaDB-backed CRUD, query operations, and lossless round-trip storage.

**Areas covered:**
- Initialisation (in-memory and persistent)
- `store_form` / `retrieve_form` / `update_form` / `delete_form`
- `get_forms_by_context`, `search_similar_forms`, `search_by_entity`
- `list_contexts`, `get_context_stats`, `count_all_forms`
- **Lossless round-trip** — `entity_id`, `relation_id`, `relation_type`, entity metadata, and form metadata are all preserved through `store_form` → `retrieve_form`
- Error handling (missing form, missing embedding)

**Key invariant:** Every field on `LogicalForm` survives a store/retrieve cycle unchanged. The `_build_metadata` helper serialises the full form as JSON (`form_json`) alongside scalar metadata fields used for ChromaDB `WHERE` filtering.

**Example:**

```python
from glcs.core.memory_manager import MemoryManager
from glcs.core.semantic_encoder import SemanticEncoder
from glcs.core.models import LogicalForm, Entity, Relation, LogicalType, Polarity

manager = MemoryManager(in_memory=True)
encoder = SemanticEncoder()

form = LogicalForm(
    context_id="ctx",
    logical_type=LogicalType.GROUND_FACT,
    subject=Entity(name="alice", entity_type="person", metadata={"role": "admin"}),
    predicate=Relation(verb="manages", relation_type="hierarchy"),
    object=Entity(name="bob"),
    polarity=Polarity.POSITIVE,
    source_text="Alice manages Bob",
    metadata={"source": "hr-system"},
)

encoder.add_embedding_to_form(form)
original_subject_id = form.subject.entity_id

form_id = manager.store_form(form)
retrieved = manager.retrieve_form(form_id)

assert retrieved.subject.entity_id == original_subject_id      # ID preserved
assert retrieved.predicate.relation_type == "hierarchy"         # relation_type preserved
assert retrieved.subject.metadata == {"role": "admin"}          # metadata preserved
assert retrieved.metadata == {"source": "hr-system"}            # form metadata preserved
```

---

### `test_consistency_checker.py` — 23 tests

Tests contradiction and redundancy detection algorithms.

**Areas covered:**
- Polarity contradiction detection (vectorised, O(n²) eliminated)
- Paraphrase contradiction detection (embedding similarity ≥ 0.8)
- Universal vs ground fact contradiction
- Exact redundancy (identical source text)
- Semantic redundancy (high cosine similarity, same polarity)
- Severity scoring (HIGH for universal contradictions, LOW for redundancies)
- Violation summary generation
- Performance guard (vectorised batch does not regress)

---

### `test_llm_parser.py` — 35 tests

Tests `LLMLogicalParser` with all LLM calls mocked.

**Areas covered:**
- Initialisation (provider, model, cache settings)
- Parsing all `LogicalType` variants
- Entity normalisation and type extraction
- Input validation and error handling
- LRU cache (hit, miss, clear, size stats)
- Batch processing
- Provider switching

> These are unit tests — all LLM calls are mocked. No API key required.

---

### `test_semantic_encoder.py` — 35 tests

Tests `SemanticEncoder` (sentence-transformers wrapper).

**Areas covered:**
- Single and batch encoding
- Embedding normalisation
- Cosine similarity calculations
- Thread-safe singleton model cache
- Integration with `LogicalForm.embedding`

---

### `test_providers/test_provider_system.py` — 23 tests

Tests the provider factory and all five LLM provider implementations.

**Providers tested:** OpenAI, Anthropic (Claude), Gemini, Groq, Ollama

**Areas covered:**
- `ProviderFactory` registration (idempotent re-registration, duplicate class collision)
- `ProviderConfig` defaults and masking
- Provider import and construction
- API key validation at construction time (not deferred)
- Provider auto-registration on import

---

### `test_config_manager.py` — 13 tests

Tests YAML configuration loading, validation, and key access.

### `test_exceptions.py` — 16 tests

Tests the custom exception hierarchy (`GLCSException`, `GLCSMemoryError`, `ConsistencyError`, etc.).

### `test_logger.py` — 7 tests

Tests structured logging setup and `get_logger()`.

---

## Integration Tests (`integration/`)

`test_advanced_glcs.py` tests the full `AdvancedGLCS` orchestrator — parse, encode, store, check. LLM calls are mocked; ChromaDB and SemanticEncoder run for real.

---

## Test-Driven Development

Per [BUILD_PRINCIPLES.md](../docs/BUILD_PRINCIPLES.md), **all new features must follow TDD**:

1. Write a failing test that defines the expected behaviour
2. Write the minimum implementation to make it pass
3. Refactor

Tests must cover:
- The **happy path** (expected input, expected output)
- **Edge cases** (empty inputs, boundary values)
- **Failure modes** (invalid input, missing data, external errors)

No pull request is complete without tests.

---

## Writing Good Tests

**Do:**
- One assertion focus per test function
- Descriptive names: `test_store_retrieve_preserves_entity_ids`
- Use `pytest.fixture` for shared setup
- Test behaviour, not implementation details
- Keep tests fully independent (no shared mutable state)

**Don't:**
- Use `assert True` or `assert isinstance(x, object)`
- Swallow exceptions with bare `except: pass`
- Call real external APIs from unit tests — mock them
- Write tests that depend on execution order

---

## Test Status by Stage

| Stage | Component | Status | Tests |
|-------|-----------|--------|-------|
| 0.2 | Config & Utilities | ✅ Complete | 36 |
| 0.3 | Data Models | ✅ Complete | 50 |
| 1.1 | Semantic Encoder | ✅ Complete | 35 |
| 1.2 | Memory Manager | ✅ Complete | 34 |
| 1.3 | Consistency Checker | ✅ Complete | 23 |
| 1.4 | LLM Logical Parser | ✅ Complete | 35 |
| 1.5 | Provider System | ✅ Complete | 23 |
| 2.1 | REST API | ⏳ In progress | — |
| 2.2 | WebSocket | ⏳ Not started | — |

**Total unit tests: 234**
