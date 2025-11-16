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

## Next Steps

After Stage 0.3 (Data Models), the following components will use these models:

- **Stage 1.1:** Semantic Encoder (adds `embedding` to LogicalForm)
- **Stage 1.2:** Memory Manager (stores LogicalForm objects)
- **Stage 1.3:** Consistency Checker (creates Violation and ConsistencyReport)
- **Stage 1.4:** Logical Parser (creates LogicalForm objects)

---

## References

- **Pydantic Documentation:** https://docs.pydantic.dev/
- **Type Hints:** https://docs.python.org/3/library/typing.html
- **UUID Standard:** https://datatracker.ietf.org/doc/html/rfc4122

---

**Last Updated**: Stage 0.3 (Data Models Complete)
**Test Coverage**: 99% (42 tests, all passing)
