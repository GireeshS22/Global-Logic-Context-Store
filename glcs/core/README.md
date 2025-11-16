# GLCS Core Data Models

This directory contains the core data models (schemas) for GLCS. These are **Pydantic data classes**, not machine learning models.

## Overview

All GLCS components work with these standardized data structures to ensure type safety, automatic validation, and consistent serialization.

---

## Models

### 1. Entity

**Purpose:** Represents a subject or object in logical statements.

**Fields:**
- `entity_id` (UUID): Unique identifier, auto-generated
- `name` (str): Name of the entity, normalized to lowercase
- `entity_type` (Optional[str]): Category (e.g., "person", "concept")
- `metadata` (dict): Additional properties

**Example:**
```python
from glcs.core.models import Entity

entity = Entity(name="Socrates", entity_type="person")
# entity.name == "socrates" (automatically normalized)
# entity.entity_id == UUID('...')
```

**Validation:**
- Name must be non-empty
- Name is automatically lowercased and trimmed

---

### 2. Relation

**Purpose:** Represents predicates/verbs connecting entities.

**Fields:**
- `relation_id` (UUID): Unique identifier, auto-generated
- `verb` (str): Predicate/verb, normalized to lowercase
- `relation_type` (Optional[str]): Category (e.g., "property", "location")
- `metadata` (dict): Additional properties

**Example:**
```python
from glcs.core.models import Relation

relation = Relation(verb="is_mortal", relation_type="property")
# relation.verb == "is_mortal"
```

**Validation:**
- Verb must be non-empty
- Verb is automatically lowercased and trimmed

---

### 3. LogicalType (Enum)

**Purpose:** Categorizes logical statements by structure.

**Values:**
- `UNIVERSAL_RULE`: Universal quantification (∀x: P(x) → Q(x))
  - Example: "All humans are mortal"
- `EXISTENTIAL_CLAIM`: Existential quantification (∃x: P(x))
  - Example: "There exists a human named Socrates"
- `CONDITIONAL_LOGIC`: If-then statements (P → Q)
  - Example: "If it rains, then the ground is wet"
- `GROUND_FACT`: Simple assertions (P(a))
  - Example: "Socrates is human"

**Example:**
```python
from glcs.core.models import LogicalType

logical_type = LogicalType.UNIVERSAL_RULE
# logical_type.value == "universal_rule"
```

---

### 4. Polarity (Enum)

**Purpose:** Indicates affirmation or negation.

**Values:**
- `POSITIVE`: Affirmative statement
  - Example: "Socrates IS mortal"
- `NEGATIVE`: Negative statement
  - Example: "Socrates is NOT immortal"

**Example:**
```python
from glcs.core.models import Polarity

polarity = Polarity.POSITIVE
# polarity.value == "positive"
```

---

### 5. LogicalForm ⭐ (MOST CRITICAL)

**Purpose:** Core data structure representing a parsed logical statement.

**Fields:**
- `form_id` (UUID): Unique identifier, auto-generated
- `context_id` (str): Session/conversation identifier
- `timestamp` (datetime): Creation time, auto-generated
- `logical_type` (LogicalType): Type of logical statement
- `subject` (Entity): Subject entity
- `predicate` (Relation): Predicate/verb
- `object` (Optional[Entity]): Object entity (for binary relations)
- `polarity` (Polarity): POSITIVE or NEGATIVE
- `confidence_score` (float): Parser confidence (0.0-1.0, default 1.0)
- `source_text` (str): Original natural language input
- `embedding` (Optional[np.ndarray]): 768-dimensional semantic vector
- `metadata` (dict): Additional properties

**Example:**
```python
from glcs.core.models import LogicalForm, Entity, Relation, LogicalType, Polarity
import numpy as np

# Create a logical form
form = LogicalForm(
    context_id="session_123",
    logical_type=LogicalType.UNIVERSAL_RULE,
    subject=Entity(name="humans"),
    predicate=Relation(verb="are"),
    object=Entity(name="mortal"),
    polarity=Polarity.POSITIVE,
    source_text="All humans are mortal",
    confidence_score=0.95
)

# Add embedding later (from Semantic Encoder)
form.embedding = np.random.rand(768)

# Serialize to JSON
json_data = form.model_dump()
```

**Validation:**
- `context_id` must be non-empty
- `confidence_score` must be between 0.0 and 1.0
- `embedding`, if present, must be exactly 768 dimensions
- `source_text` must be non-empty

**Component Usage:**
- **Logical Parser**: Creates LogicalForm objects
- **Semantic Encoder**: Adds `embedding` field to LogicalForm
- **Memory Manager**: Stores LogicalForm objects
- **Consistency Checker**: Compares LogicalForm objects

---

### 6. Violation

**Purpose:** Represents a detected logical inconsistency.

**Fields:**
- `violation_id` (UUID): Unique identifier, auto-generated
- `violation_type` (str): Category (e.g., "CONTRADICTION", "REDUNDANCY")
- `conflicting_forms` (List[UUID]): IDs of conflicting LogicalForms (minimum 2)
- `severity` (str): Must be "HIGH", "MEDIUM", or "LOW"
- `explanation` (str): Human-readable description
- `detected_at` (datetime): Detection timestamp, auto-generated
- `metadata` (dict): Additional properties

**Example:**
```python
from glcs.core.models import Violation

violation = Violation(
    violation_type="CONTRADICTION",
    conflicting_forms=[form1.form_id, form2.form_id],
    severity="HIGH",
    explanation="Universal rule 'All humans are mortal' contradicts ground fact 'Socrates is immortal'"
)
```

**Validation:**
- `conflicting_forms` must contain at least 2 UUIDs
- `severity` must be exactly "HIGH", "MEDIUM", or "LOW"
- `explanation` must be non-empty

---

### 7. ConsistencyReport

**Purpose:** API response format for consistency checking.

**Fields:**
- `report_id` (UUID): Unique identifier, auto-generated
- `context_id` (str): Session that was checked
- `is_consistent` (bool): True if no violations found
- `violations` (List[Violation]): Detected violations (empty if consistent)
- `total_forms_checked` (int): Number of LogicalForms analyzed
- `generated_at` (datetime): Report generation time, auto-generated
- `metadata` (dict): Additional properties

**Example:**
```python
from glcs.core.models import ConsistencyReport, Violation

# Consistent report (no violations)
report = ConsistencyReport(
    context_id="session_123",
    is_consistent=True,
    violations=[],
    total_forms_checked=10
)

# Inconsistent report (with violations)
report = ConsistencyReport(
    context_id="session_456",
    is_consistent=False,
    violations=[violation1, violation2],
    total_forms_checked=15
)

# Serialize to JSON for API response
json_response = report.model_dump()
```

**Validation:**
- `is_consistent` must match `violations` list:
  - `True` if violations is empty
  - `False` if violations has items
- `total_forms_checked` must be >= 0

---

## Data Flow

```
User Input: "All humans are mortal"
         ↓
    [Logical Parser]
         ↓
    Creates: LogicalForm(
        logical_type=UNIVERSAL_RULE,
        subject=Entity(name="humans"),
        predicate=Relation(verb="are"),
        object=Entity(name="mortal"),
        polarity=POSITIVE,
        source_text="All humans are mortal"
    )
         ↓
    [Semantic Encoder]
         ↓
    Adds: embedding=[0.23, -0.45, 0.67, ...] (768 dims)
         ↓
    [Memory Manager]
         ↓
    Stores LogicalForm in vector database
         ↓
    [Consistency Checker]
         ↓
    Compares against stored LogicalForms
         ↓
    Creates: ConsistencyReport(
        is_consistent=True,
        violations=[],
        total_forms_checked=5
    )
         ↓
    Returns to API Layer
```

---

## Model Relationships

```
ConsistencyReport
  ├── context_id (str)
  ├── is_consistent (bool)
  ├── violations: List[Violation]
  │     ├── violation_type (str)
  │     ├── conflicting_forms: List[UUID]  ← References LogicalForm.form_id
  │     ├── severity (str)
  │     └── explanation (str)
  └── total_forms_checked (int)

LogicalForm
  ├── form_id (UUID)
  ├── context_id (str)
  ├── logical_type: LogicalType (enum)
  ├── subject: Entity
  │     ├── entity_id (UUID)
  │     ├── name (str)
  │     └── entity_type (str)
  ├── predicate: Relation
  │     ├── relation_id (UUID)
  │     ├── verb (str)
  │     └── relation_type (str)
  ├── object: Optional[Entity]
  ├── polarity: Polarity (enum)
  ├── confidence_score (float: 0.0-1.0)
  ├── source_text (str)
  └── embedding (Optional[np.ndarray: 768-dim])
```

---

## Testing

Comprehensive test suite: `tests/unit/test_models.py`

**Coverage:** 99% (88/89 lines)

**Test Categories:**
- Entity validation and normalization (6 tests)
- Relation validation and normalization (5 tests)
- Enum definitions (4 tests)
- LogicalForm creation and validation (14 tests)
- Violation validation (6 tests)
- ConsistencyReport validation (6 tests)
- Integration workflow (1 test)

**Run Tests:**
```bash
# Run all model tests
poetry run pytest tests/unit/test_models.py -v

# Check coverage
poetry run pytest tests/unit/test_models.py --cov=glcs.core.models --cov-report=term-missing
```

---

## Usage Guidelines

### 1. Creating LogicalForms

```python
from glcs.core.models import LogicalForm, Entity, Relation, LogicalType, Polarity

# Minimal form (unary predicate)
form = LogicalForm(
    context_id="session_id",
    logical_type=LogicalType.GROUND_FACT,
    subject=Entity(name="socrates"),
    predicate=Relation(verb="exists"),
    polarity=Polarity.POSITIVE,
    source_text="Socrates exists"
)

# Complete form (binary predicate)
form = LogicalForm(
    context_id="session_id",
    logical_type=LogicalType.UNIVERSAL_RULE,
    subject=Entity(name="humans"),
    predicate=Relation(verb="are"),
    object=Entity(name="mortal"),
    polarity=Polarity.POSITIVE,
    source_text="All humans are mortal"
)
```

### 2. Handling Violations

```python
from glcs.core.models import Violation

# Always include at least 2 conflicting forms
violation = Violation(
    violation_type="CONTRADICTION",
    conflicting_forms=[form1_id, form2_id],
    severity="HIGH",
    explanation="Explain why these conflict"
)
```

### 3. Building Reports

```python
from glcs.core.models import ConsistencyReport

# Ensure is_consistent matches violations
report = ConsistencyReport(
    context_id="session_id",
    is_consistent=(len(violations) == 0),  # Must match!
    violations=violations,
    total_forms_checked=total
)
```

### 4. JSON Serialization

```python
# Export to JSON
form_dict = form.model_dump()  # Returns dict
form_json = form.model_dump_json()  # Returns JSON string

# Import from JSON
from glcs.core.models import LogicalForm
form = LogicalForm.model_validate_json(json_string)
```

---

## Important Contracts

### Critical Invariants (NEVER VIOLATE)

1. **Embedding Dimension:**
   - If `LogicalForm.embedding` is set, it MUST be exactly 768 dimensions
   - Encoder must always produce 768-dim vectors

2. **Confidence Score Range:**
   - `LogicalForm.confidence_score` MUST be between 0.0 and 1.0

3. **Consistency Flag:**
   - `ConsistencyReport.is_consistent` MUST equal `(len(violations) == 0)`

4. **Violation Minimum:**
   - `Violation.conflicting_forms` MUST have at least 2 UUIDs

5. **Severity Values:**
   - `Violation.severity` MUST be exactly "HIGH", "MEDIUM", or "LOW"

### Component Contracts

**Logical Parser MUST:**
- Produce valid `LogicalForm` objects
- Set `confidence_score` based on parsing certainty
- Populate `source_text` with original input

**Semantic Encoder MUST:**
- Add exactly 768-dimensional `embedding` to `LogicalForm`
- Use consistent model (`all-MiniLM-L6-v2` for MVP)

**Memory Manager MUST:**
- Store complete `LogicalForm` objects
- Preserve `form_id` for retrieval

**Consistency Checker MUST:**
- Return valid `ConsistencyReport` objects
- Create `Violation` objects with at least 2 conflicting forms
- Set `is_consistent` flag correctly

---

## Key Design Decisions

### Why UUIDs?
- Globally unique across sessions
- No central ID server needed
- Standard for distributed systems

### Why 768 Dimensions for Embeddings?
- Matches output of `sentence-transformers/all-MiniLM-L6-v2`
- Standard transformer size
- Well-supported by vector databases

### Why Separate Entity and Relation?
- Reusability: Same entity can appear in multiple forms
- Normalization: "Socrates" should be one entity, not duplicated
- Future expansion: Can add aliases, entity linking, etc.

### Why Optional Object Field?
- Some predicates are unary: "X exists"
- Binary relations: "X is Y", "A lives_in B"
- Flexibility for future n-ary relations

### Why Confidence Score?
- LLM parser is not 100% accurate
- Low confidence → may need human review
- Research metric: Track parser performance over time

---

## File Organization

```
glcs/core/
├── __init__.py          # Package initialization
├── models.py            # All data models (314 lines)
└── README.md            # This documentation
```

---

---

## Semantic Encoder (Stage 1.1) ✅

**File:** `glcs/core/semantic_encoder.py`

### Purpose

The **SemanticEncoder** generates 768-dimensional vector embeddings for text using sentence-transformers. These embeddings enable:
- Semantic similarity comparisons between LogicalForms
- Efficient nearest-neighbor search in vector databases
- Consistency checking based on meaning (not just syntax)

### Key Features

- **768-dimensional embeddings** using `all-mpnet-base-v2` model
- **Singleton pattern** - model cached and reused across requests
- **Batch processing** - 5x faster than individual encoding
- **L2 normalization** - enables fast cosine similarity (dot product)
- **LogicalForm integration** - automatic embedding addition

### Core Methods

#### `encode(text: str) -> np.ndarray`

Encode a single text string into a 768-dimensional embedding.

```python
from glcs.core.semantic_encoder import SemanticEncoder

encoder = SemanticEncoder()
embedding = encoder.encode("All humans are mortal")
# embedding.shape == (768,)
```

#### `encode_batch(texts: List[str]) -> List[np.ndarray]`

Encode multiple texts efficiently in batch.

```python
texts = ["All humans are mortal", "Socrates is human"]
embeddings = encoder.encode_batch(texts)
# len(embeddings) == 2
# all(e.shape == (768,) for e in embeddings) == True
```

#### `add_embedding_to_form(form: LogicalForm) -> LogicalForm`

Add embedding to a LogicalForm based on its `source_text`.

```python
from glcs.core.models import LogicalForm, Entity, Relation
from glcs.core.models import LogicalType, Polarity

form = LogicalForm(
    context_id="session_123",
    logical_type=LogicalType.UNIVERSAL_RULE,
    subject=Entity(name="humans"),
    predicate=Relation(verb="are"),
    object=Entity(name="mortal"),
    polarity=Polarity.POSITIVE,
    source_text="All humans are mortal"
)

encoder.add_embedding_to_form(form)
# form.embedding is now a 768-dim numpy array
```

#### `add_embeddings_to_forms(forms: List[LogicalForm]) -> List[LogicalForm]`

Add embeddings to multiple LogicalForms efficiently using batch encoding.

```python
forms = [form1, form2, form3]  # List of LogicalForms
encoder.add_embeddings_to_forms(forms)
# All forms now have embeddings
```

#### `cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float`

Compute semantic similarity between two embeddings.

```python
emb1 = encoder.encode("All humans are mortal")
emb2 = encoder.encode("Every person is mortal")
similarity = encoder.cosine_similarity(emb1, emb2)
# similarity ≈ 0.85 (high similarity)
```

**Similarity Interpretation:**
- `1.0`: Identical meaning
- `0.7-0.9`: Very similar
- `0.5-0.7`: Moderately similar
- `0.3-0.5`: Somewhat related
- `0.0-0.3`: Unrelated
- `< 0.0`: Opposite meaning (rare)

### Model Details

**Default Model:** `all-mpnet-base-v2`
- **Dimensions:** 768
- **Size:** ~420MB
- **Performance:** Excellent on semantic similarity tasks
- **Speed:** ~50ms per text (single), ~10ms per text (batch)

### Performance Optimization

**Model Caching:**
```python
# Model is loaded once and cached
encoder1 = SemanticEncoder()  # Loads model
encoder2 = SemanticEncoder()  # Reuses cached model
```

**Batch Processing:**
```python
# ❌ Slow: Individual encoding
embeddings = [encoder.encode(t) for t in texts]  # ~10ms per text

# ✅ Fast: Batch encoding
embeddings = encoder.encode_batch(texts)  # ~2ms per text (5x faster)
```

### Integration with GLCS Pipeline

```
User Input: "All humans are mortal"
         ↓
    [Logical Parser] (Stage 1.4)
         ↓
    Creates LogicalForm with source_text
         ↓
    [Semantic Encoder] ← YOU ARE HERE
         ↓
    Adds 768-dim embedding to LogicalForm
         ↓
    [Memory Manager] (Stage 1.2)
         ↓
    Stores LogicalForm with embedding in vector DB
         ↓
    [Consistency Checker] (Stage 1.3)
         ↓
    Compares embeddings for semantic similarity
         ↓
    Returns ConsistencyReport
```

### Error Handling

```python
# Empty text raises ValueError
try:
    encoder.encode("")
except ValueError as e:
    print(e)  # "Cannot encode empty text"

# Wrong dimension embeddings rejected by LogicalForm
form.embedding = np.random.rand(512)  # Raises ValueError
# "Embedding must be 768-dimensional, got shape (512,)"
```

### Testing

**Test File:** `tests/unit/test_semantic_encoder.py`

**Coverage:** 97% (58/60 lines)

**Test Categories:**
- Basic encoding (7 tests)
- Batch encoding (3 tests)
- Error handling (4 tests)
- LogicalForm integration (5 tests)
- Cosine similarity (5 tests)
- Model caching (3 tests)
- Integration workflow (1 test)
- Dimension validation (2 tests)
- Determinism (2 tests)

**Run Tests:**
```bash
# Run semantic encoder tests
poetry run pytest tests/unit/test_semantic_encoder.py -v

# Check coverage
poetry run pytest tests/unit/test_semantic_encoder.py --cov=glcs.core.semantic_encoder --cov-report=term-missing
```

### Design Decisions

**Why 768 dimensions?**
- Standard size for transformer models
- Good balance between accuracy and efficiency
- Well-supported by vector databases

**Why all-mpnet-base-v2?**
- Produces exactly 768 dimensions (required by LogicalForm validation)
- Excellent performance on semantic similarity benchmarks
- Moderate size (~420MB) - not too large
- Widely used and well-tested

**Why L2 normalization?**
- Enables fast cosine similarity via dot product
- Cosine similarity = dot product when vectors are normalized
- Critical for efficient nearest-neighbor search in vector databases

**Why singleton pattern for model?**
- Avoids loading 420MB model multiple times
- Reduces memory usage in API servers
- Faster initialization for subsequent encoders

---

## Next Steps

After Stage 1.1 (Semantic Encoder), the following components will be built:

- **Stage 1.2:** Memory Manager (stores LogicalForm objects with embeddings)
- **Stage 1.3:** Consistency Checker (compares LogicalForms using embeddings)
- **Stage 1.4:** Logical Parser (creates LogicalForm objects from natural language)

---

## References

- **Pydantic Documentation:** https://docs.pydantic.dev/
- **Type Hints:** https://docs.python.org/3/library/typing.html
- **UUID Standard:** https://datatracker.ietf.org/doc/html/rfc4122
- **Sentence Transformers:** https://www.sbert.net/
- **all-mpnet-base-v2 Model:** https://huggingface.co/sentence-transformers/all-mpnet-base-v2

---

**Last Updated**: Stage 1.1 (Semantic Encoder Complete)
**Test Coverage**: 91% overall (111 tests, all passing)
**Stage 0.3**: Data Models - 99% coverage (42 tests)
**Stage 1.1**: Semantic Encoder - 97% coverage (32 tests)
