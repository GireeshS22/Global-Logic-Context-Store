# GLCS Cascade Review Document

**Purpose**: Track dependencies between components and identify potential cascade effects when making changes.

**Version**: Stage 0.1
**Last Updated**: 2025-11-16

---

## What is a Cascade Review?

A cascade review identifies:
1. **Dependencies**: What components depend on what
2. **Contracts**: APIs and interfaces that must remain stable
3. **Impact Analysis**: What breaks if X changes
4. **Migration Paths**: How to safely make breaking changes

This document is updated after each stage to track cumulative dependencies.

---

## Stage 0.1: Project Structure Setup

### ✅ Decisions Made (Fixed)

1. **Package Manager: Poetry**
   - All dependency management uses Poetry
   - No pip/virtualenv/conda
   - **Impact**: All documentation and scripts reference `poetry run`

2. **Python Version: 3.11+**
   - Required by numpy 2.3.4
   - **Impact**: Cannot support Python 3.10 or earlier

3. **Project Structure**
   ```
   glcs/
   ├── core/
   ├── hierarchical/
   ├── utils/
   └── api/
   ```
   - **Impact**: All import paths follow this structure
   - **Example**: `from glcs.core.models import LogicalForm`

4. **Package Name: `glcs`**
   - Defined in pyproject.toml
   - **Impact**: All imports start with `glcs.`
   - **Breaking change if renamed**: All code breaks

5. **Dependencies (Core)**
   - numpy ^2.3.4
   - pydantic ^2.12.4
   - python-dotenv ^1.2.1
   - **Impact**: Code can use features from these versions

6. **Dependencies (Dev)**
   - pytest ^8.0.0
   - pytest-cov ^4.1.0
   - black ^24.0.0
   - ruff ^0.3.0
   - **Impact**: Code formatting and testing standards

### ⚠️ Potential Cascade Effects

#### If Poetry is Removed/Changed
**Impact**: HIGH - Breaks all setup
- Need to:
  - Convert pyproject.toml to setup.py or requirements.txt
  - Update all documentation
  - Update CI/CD pipelines
  - Retrain users/developers
- **Recommendation**: Don't change this

#### If Python Version Changes
**Impact**: MEDIUM
- To Python 3.12+: Likely compatible, retest
- To Python 3.10: Need older numpy, may break features
- **Action needed**:
  - Update pyproject.toml
  - Reinstall dependencies
  - Rerun all tests

#### If Package Name Changes
**Impact**: CRITICAL - Breaks everything
- Need to:
  - Update pyproject.toml
  - Rename glcs/ directory
  - Find/replace all imports in codebase
  - Update all documentation
  - Update published packages
- **Recommendation**: NEVER change after first release

#### If Folder Structure Changes
**Impact**: MEDIUM-HIGH
- Adding new modules (e.g., `glcs/inference/`): LOW impact, just create
- Renaming modules (e.g., `core` → `components`): HIGH impact, breaks imports
- Moving files between modules: MEDIUM impact, update imports
- **Action needed**:
  - Create new __init__.py files
  - Update imports across codebase
  - Update READMEs
  - Update tests

#### If Core Dependencies Change
**Impact**: MEDIUM
- Upgrading (e.g., pydantic 2.x → 3.x):
  - Review changelog for breaking changes
  - Update code to match new API
  - Rerun all tests
- Removing (e.g., remove numpy):
  - CRITICAL if code uses it
  - Need alternative implementation
- **Action needed**:
  - `poetry update <package>`
  - Fix any breaking changes
  - Test thoroughly

### 🔄 What Can Be Changed Safely

1. ✅ **Add new folders** (e.g., `glcs/inference/`)
   - Impact: None, just create and document

2. ✅ **Add new dependencies**
   - Use: `poetry add <package>`
   - Impact: Increases install size, minimal

3. ✅ **Update READMEs**
   - Impact: None on code

4. ✅ **Add new test directories**
   - Impact: None, just organize

5. ✅ **Add .gitignore entries**
   - Impact: None on code

### 📋 Checklist for Future Changes

Before making structural changes, ask:

1. ❓ **Does this break existing imports?**
   - If yes: Need find/replace across codebase

2. ❓ **Does this require dependency changes?**
   - If yes: Update pyproject.toml, test compatibility

3. ❓ **Does this affect the public API?**
   - If yes: Version bump, migration guide

4. ❓ **Does this require documentation updates?**
   - Always: Update relevant READMEs

5. ❓ **Does this affect tests?**
   - If yes: Update test imports, fixtures

---

## Stage 0.2: Configuration System (Coming Next)

**Anticipated Dependencies**:
- All components will load `config/glcs_config.yaml`
- **Future cascade**: Changing config schema requires updating all components that read config
- **Future cascade**: Logger setup affects all modules using logging

**Will document in Stage 0.2**.

---

## Stage 0.3: Data Models (Coming Next)

**Anticipated Dependencies**:
- LogicalForm schema becomes a CONTRACT
- **Future cascade**: Changing LogicalForm fields breaks parser, encoder, memory, checker
- **Future cascade**: Enum values (LogicalType, Polarity) are referenced throughout codebase

**Will document in Stage 0.3**.

---

## Dependency Graph (Current)

```
pyproject.toml (defines)
    ↓
Dependencies installed by Poetry
    ↓
glcs package structure
    ↓
Tests import from glcs
```

**Critical Path**: pyproject.toml → Poetry install → glcs imports work

---

## Migration Strategies

### If We Must Change Package Name

1. Create new package with new name
2. Implement forwarding imports in old package
3. Deprecation warning for 1 version
4. Remove old package

**Example**:
```python
# In old glcs/__init__.py
import warnings
warnings.warn("glcs is deprecated, use glcs_new", DeprecationWarning)
from glcs_new import *
```

### If We Must Change Folder Structure

1. Keep old structure
2. Create symlinks/aliases to new structure
3. Update documentation showing new structure
4. Deprecate old structure
5. Remove after transition period

---

## Questions to Ask Before Each Stage

1. **What contracts am I creating?**
   - APIs, data schemas, config formats

2. **What depends on this?**
   - List all current and future dependents

3. **How painful to change later?**
   - Rate: Easy / Medium / Hard / Critical

4. **Do I need versioning?**
   - If public API, yes

5. **What's the rollback plan?**
   - Can I undo this change easily?

---

## Stage Completion Status

- ✅ **Stage 0.1**: Complete
  - Dependencies: Poetry, Python 3.11, package structure
  - Contracts: Import paths, package name
  - Risk: Changing these is HIGH impact

- ✅ **Stage 0.2**: Complete
  - Dependencies: PyYAML, config schema, exception hierarchy
  - Contracts: Config file structure, logger usage pattern, exception types
  - Risk: Config schema changes are HIGH impact, exceptions are MEDIUM impact

- ⏳ **Stage 0.3**: Not started

---

## Stage 0.2: Configuration System - Cascade Analysis

### ✅ Decisions Made (Fixed Contracts)

1. **Configuration Schema Structure**
   ```yaml
   memory:
     vector_dimension: 768
     similarity_threshold: 0.85
     initial_capacity: 1000

   consistency:
     direct_contradiction_threshold: 0.85
     confidence_threshold: 0.5

   encoder:
     model_name: "sentence-transformers/all-MiniLM-L6-v2"
     batch_size: 32

   parser:
     llm_provider: "openai"
     model: "gpt-4o-mini"
     max_retries: 3
     timeout: 30

   logging:
     level: "INFO"
     format: "simple"
   ```
   - **Impact**: All components depend on this structure
   - **Contract**: Nested YAML with 5 required sections

2. **Required Configuration Sections**
   - `memory`, `consistency`, `encoder`, `parser`, `logging`
   - **Impact**: Config validation enforces these sections
   - **Breaking change if modified**: Must update validation + all code reading config

3. **Vector Dimension: 768**
   - Fixed based on encoder model choice (all-MiniLM-L6-v2 → 768-dim after projection)
   - **CRITICAL**: Memory manager, encoder, and all vector operations depend on this
   - **Changing requires**: Re-encode all data, clear memory, update all components

4. **Exception Hierarchy**
   ```
   GLCSException (base)
   ├── ConfigurationError
   ├── MemoryError
   ├── ConsistencyError
   ├── ValidationError
   └── ParsingError
   ```
   - **Impact**: All error handling uses these exceptions
   - **Contract**: Never use generic Exception, always use specific GLCS exceptions

5. **Logger Usage Pattern**
   ```python
   from glcs.utils.logger import get_logger
   logger = get_logger(__name__)
   ```
   - **Impact**: All modules must follow this pattern
   - **Contract**: Don't use print() or raw logging module

6. **Configuration Loading Pattern**
   ```python
   from glcs.utils.config_manager import load_config
   config = load_config("config/glcs_config.yaml")
   ```
   - **Impact**: All components use this centralized approach
   - **Contract**: Don't hardcode parameters

### ⚠️ Cascade Effects - What Changes Break What

#### If Config Schema Changes

**Scenario**: Add new section or rename existing section

**Impact**: CRITICAL
- **Breaks**:
  - `config_manager.validate_config()` (needs updated REQUIRED_SECTIONS)
  - All components reading that section
  - All tests expecting old structure
  - Documentation (config/README.md, glcs/utils/README.md)

**Action needed**:
1. Update `REQUIRED_SECTIONS` in `config_manager.py`
2. Update validation logic
3. Update `config/glcs_config.yaml`
4. Update all components reading the changed section
5. Update tests
6. Update documentation
7. Consider config versioning

**Example**:
```python
# Adding new section 'inference'
REQUIRED_SECTIONS = ["memory", "consistency", "encoder", "parser", "logging", "inference"]
# Must also add inference section to config file
# Must update validation tests
```

#### If Config Parameter Changes

**Scenario**: Change `memory.vector_dimension` from 768 to 1024

**Impact**: CRITICAL
- **Breaks**:
  - Encoder (must use model that outputs 1024-dim)
  - Memory manager (expects 768-dim vectors)
  - All stored vectors (wrong dimension)
  - Similarity search (dimension mismatch)

**Action needed**:
1. Change encoder model to one that outputs 1024-dim
2. Update `vector_dimension` in config
3. **Clear all stored memory** (old vectors incompatible)
4. Re-encode all data
5. Update tests

**Recommendation**: DON'T change vector dimension after deployment

#### If Exception Types Change

**Scenario**: Add new exception type `InferenceError`

**Impact**: LOW-MEDIUM
- **Breaks**: Nothing (backward compatible)
- **Needs updates**:
  - `glcs/utils/exceptions.py` (add new class)
  - `tests/unit/test_exceptions.py` (add tests)
  - `glcs/utils/README.md` (document new exception)

**Action needed**:
1. Add exception class inheriting from GLCSException
2. Add docstring with usage examples
3. Add tests
4. Document in README

**Example**:
```python
class InferenceError(GLCSException):
    """Raised when inference operations fail."""
    pass
```

#### If Logger Format Changes

**Scenario**: Change from `simple` to `json` format in config

**Impact**: LOW
- **Breaks**: Nothing (just changes output format)
- **Affects**: Log parsing scripts (if any)

**Action needed**:
1. Update `config/glcs_config.yaml` or `config/logging.yaml`
2. Update log parsing tools (if any)
3. Restart application

#### If PyYAML is Removed/Replaced

**Impact**: HIGH
- **Breaks**:
  - Config loading (uses PyYAML)
  - Logger setup (uses PyYAML)

**Action needed**:
1. Find alternative (e.g., TOML, JSON)
2. Convert all config files to new format
3. Update `load_config()` implementation
4. Update `setup_logging()` implementation
5. Update all tests
6. Update documentation

**Recommendation**: DON'T change this - PyYAML is standard

### 🔄 What CAN Be Changed Safely

1. ✅ **Add new config parameters** (within existing sections)
   - Impact: None if optional
   - Just add to config file and access with `get_config_value(..., default=X)`

2. ✅ **Change parameter values** (not structure)
   - Example: `similarity_threshold: 0.85` → `0.90`
   - Impact: Changes behavior but doesn't break code
   - Test after changing

3. ✅ **Add new exception types**
   - Must inherit from GLCSException
   - Backward compatible
   - Add tests and documentation

4. ✅ **Change log levels**
   - Impact: Changes verbosity, doesn't break code
   - Safe to change

5. ✅ **Add new utility functions** to config_manager, logger
   - Impact: None (additive change)
   - Just document them

### 🚫 What CANNOT Be Changed Without Major Work

1. ❌ **Config file format** (YAML → JSON/TOML)
   - Breaks: Everything reading config
   - Effort: Very high

2. ❌ **Remove required config sections**
   - Breaks: Validation, all code expecting that section
   - Effort: High

3. ❌ **Change exception base class** (GLCSException → something else)
   - Breaks: All exception catching code
   - Effort: Very high

4. ❌ **Remove logger functions** (get_logger, setup_logging)
   - Breaks: All modules using logger
   - Effort: Very high

### 📋 Component Dependencies (Post Stage 0.2)

```
config/glcs_config.yaml (defines)
    ↓
glcs/utils/config_manager.py (loads & validates)
    ↓
All components (memory, encoder, parser, checker)
    ↓
Use config values for behavior

config/logging.yaml (defines)
    ↓
glcs/utils/logger.py (loads & initializes)
    ↓
All modules (get_logger(__name__))
    ↓
Log to configured handlers

glcs/utils/exceptions.py (defines)
    ↓
All modules (import and raise)
    ↓
Error handling throughout system
```

### 🎯 Action Items for Future Stages

**All future components MUST**:
1. Load config using `config_manager.load_config()`
2. Use logger via `logger.get_logger(__name__)`
3. Raise specific exceptions (not generic Exception)
4. Access config values with `get_config_value()` and defaults
5. Document which config parameters they use

**Example Component Pattern**:
```python
from glcs.utils.config_manager import load_config, get_config_value
from glcs.utils.logger import get_logger
from glcs.utils.exceptions import ComponentError

class NewComponent:
    def __init__(self, config_path="config/glcs_config.yaml"):
        self.logger = get_logger(__name__)
        self.config = load_config(config_path)

        # Extract component-specific config with defaults
        self.param = get_config_value(
            self.config,
            "new_section.param",
            default=42
        )

        self.logger.info("NewComponent initialized")
```

### 📊 Stage 0.2 Impact Summary

**Created Contracts**:
- Config schema structure (5 sections, nested YAML)
- Exception hierarchy (6 exception types)
- Logger usage pattern (get_logger(__name__))
- Config loading pattern (load_config + get_config_value)

**High-Risk Changes**:
- Modifying config schema structure
- Changing vector_dimension
- Removing exception types
- Changing config file format

**Low-Risk Changes**:
- Adding new config parameters (with defaults)
- Adding new exception types (inherit from GLCSException)
- Changing config values (not structure)
- Changing log levels

**Dependencies Created**:
- All components → config_manager (for config)
- All components → logger (for logging)
- All components → exceptions (for error handling)

---

## Notes for Future Developers

1. **Import paths are sacred**: Once established, very hard to change
2. **Config schema is a contract**: Version it if you change it
3. **Data models are contracts**: Use migrations for schema changes
4. **Test for cascade effects**: When changing core components, run FULL test suite
5. **Document breaking changes**: Keep CHANGELOG.md updated

---

## Stage 0.3: Data Models - Cascade Analysis

### ✅ Decisions Made (Fixed Contracts)

1. **Pydantic Data Models (7 models)**
   - `Entity`: Represents subjects/objects
   - `Relation`: Represents predicates/verbs
   - `LogicalType` (Enum): 4 types (UNIVERSAL_RULE, EXISTENTIAL_CLAIM, CONDITIONAL_LOGIC, GROUND_FACT)
   - `Polarity` (Enum): 2 values (POSITIVE, NEGATIVE)
   - `LogicalForm`: Core data structure for parsed statements
   - `Violation`: Represents detected inconsistencies
   - `ConsistencyReport`: API response format
   - **Impact**: ALL components depend on these models
   - **Contract**: Field names, types, and validation rules

2. **LogicalForm Structure (CRITICAL CONTRACT)**
   ```python
   LogicalForm(
       form_id: UUID,
       context_id: str,
       timestamp: datetime,
       logical_type: LogicalType,
       subject: Entity,
       predicate: Relation,
       object: Optional[Entity],
       polarity: Polarity,
       confidence_score: float (0.0-1.0),
       source_text: str,
       embedding: Optional[np.ndarray (768-dim)],
       metadata: dict
   )
   ```
   - **Impact**: Parser, Encoder, Memory, Checker ALL use this exact structure
   - **Breaking change if modified**: CRITICAL - all components break

3. **Embedding Dimension: 768**
   - Fixed in `LogicalForm.embedding` validation
   - Matches sentence-transformers output
   - **CRITICAL INVARIANT**: Embedding MUST be exactly 768 dimensions if present
   - **Changing requires**: New encoder model, re-encode all data, update validation

4. **Confidence Score Range: 0.0-1.0**
   - Validated in LogicalForm
   - **Contract**: Parser must set confidence within this range
   - **Breaking change**: Parser producing values outside range will fail validation

5. **Entity/Relation Normalization**
   - Entity names: Automatically lowercased and trimmed
   - Relation verbs: Automatically lowercased and trimmed
   - **Impact**: All entity/relation comparisons rely on normalized form
   - **Contract**: Never compare raw input, always use normalized values

6. **Violation Structure**
   ```python
   Violation(
       violation_id: UUID,
       violation_type: str,
       conflicting_forms: List[UUID] (min 2),
       severity: "HIGH" | "MEDIUM" | "LOW",
       explanation: str,
       detected_at: datetime,
       metadata: dict
   )
   ```
   - **Impact**: Consistency Checker must follow this structure
   - **Contract**: Minimum 2 conflicting forms, severity must be exact string

7. **ConsistencyReport Validation**
   - `is_consistent` MUST match `violations` list
   - `True` if violations is empty, `False` otherwise
   - **Impact**: API consumers rely on this contract
   - **Contract**: Automatic validation enforces this invariant

8. **UUID Usage for IDs**
   - All models use UUIDs for identification
   - Auto-generated by default
   - **Impact**: Globally unique IDs across sessions
   - **Contract**: Never use sequential integers or other ID schemes

### ⚠️ Cascade Effects - What Changes Break What

#### If LogicalForm Fields Change

**Scenario**: Add new required field or remove existing field

**Impact**: CRITICAL - Breaks EVERYTHING
- **Breaks**:
  - Logical Parser (creates LogicalForm)
  - Semantic Encoder (adds embedding to LogicalForm)
  - Memory Manager (stores LogicalForm)
  - Consistency Checker (compares LogicalForm)
  - All tests (expect specific fields)
  - API responses (serialized LogicalForm)
  - Stored data (incompatible schema)

**Action needed**:
1. Update LogicalForm class definition
2. Update Parser to populate new fields
3. Update Encoder to handle new fields
4. Update Memory storage schema
5. Update Consistency Checker comparison logic
6. Migrate existing stored data
7. Update all tests
8. Update API documentation
9. Version bump (breaking change)

**Example**:
```python
# Adding new field 'negation_scope'
class LogicalForm(BaseModel):
    # ... existing fields ...
    negation_scope: Optional[str] = None  # Use Optional to avoid breaking existing code
```

**Recommendation**: Use Optional fields for new additions to maintain backward compatibility

#### If Embedding Dimension Changes

**Scenario**: Change from 768 to 384 or 1024 dimensions

**Impact**: CRITICAL
- **Breaks**:
  - Embedding validation in LogicalForm
  - Encoder model choice (must match dimension)
  - Memory vector storage (wrong dimension)
  - Similarity search (dimension mismatch)
  - All stored embeddings (incompatible)

**Action needed**:
1. Update LogicalForm embedding validation (768 → new_dim)
2. Change encoder model to one producing new_dim
3. Update config `memory.vector_dimension`
4. **Clear all stored memory** (old embeddings incompatible)
5. Re-encode ALL existing data
6. Update all tests with new dimension
7. Update documentation

**Cost**: VERY HIGH - essentially a full system reset

**Recommendation**: DON'T change after initial choice unless absolutely necessary

#### If Entity/Relation Normalization Logic Changes

**Scenario**: Change normalization (e.g., don't lowercase, or add stemming)

**Impact**: HIGH
- **Breaks**:
  - Entity/Relation comparison (different normalization → different results)
  - Deduplication logic (same entity may appear as duplicates)
  - Consistency checking (may miss contradictions)
  - All stored entities/relations (normalized differently)

**Action needed**:
1. Update normalization validators in Entity and Relation
2. Re-normalize all stored entities/relations
3. Re-check all consistency checks (may find new violations)
4. Update tests expecting old normalization
5. Document normalization changes

**Example**:
```python
# Changing from lowercase to stemming
@field_validator('name')
@classmethod
def normalize_name(cls, v: str) -> str:
    from nltk.stem import PorterStemmer
    stemmer = PorterStemmer()
    return stemmer.stem(v.strip().lower())  # Now stems words
```

**Recommendation**: Establish normalization rules early and stick with them

#### If LogicalType or Polarity Enums Change

**Scenario**: Add new logical type or remove existing one

**Impact**: MEDIUM-HIGH
- **Adding new type** (e.g., `PROBABILISTIC`):
  - **Breaks**: Nothing immediately (backward compatible)
  - **Needs updates**:
    - Parser to recognize new type
    - Consistency Checker to handle new type
    - Tests to cover new type
    - Documentation
  - **Impact**: LOW (additive change)

- **Removing type** (e.g., remove `EXISTENTIAL_CLAIM`):
  - **Breaks**: CRITICAL
    - Parser may still produce removed type
    - Stored data may contain removed type
    - Tests expecting removed type
  - **Action needed**:
    - Remove from enum
    - Update Parser to not produce it
    - Migrate stored data to different type
    - Update all tests
    - Version bump

**Example - Adding new type**:
```python
class LogicalType(str, Enum):
    UNIVERSAL_RULE = "universal_rule"
    EXISTENTIAL_CLAIM = "existential_claim"
    CONDITIONAL_LOGIC = "conditional_logic"
    GROUND_FACT = "ground_fact"
    PROBABILISTIC = "probabilistic"  # NEW - backward compatible
```

**Recommendation**: Adding is OK, removing requires migration

#### If Validation Rules Change

**Scenario**: Change confidence_score range from 0.0-1.0 to 0.0-10.0

**Impact**: MEDIUM
- **Breaks**:
  - Existing LogicalForms with scores in old range (still valid)
  - Parser expecting old range (must rescale)
  - Consistency Checker thresholds (may need adjustment)
  - Tests with hardcoded scores

**Action needed**:
1. Update validation in LogicalForm
2. Update Parser to produce scores in new range
3. Migrate existing scores (multiply by 10)
4. Update Consistency Checker thresholds in config
5. Update all tests
6. Document new range

**Recommendation**: Avoid changing validation ranges after deployment

#### If Pydantic Version Changes

**Scenario**: Upgrade from Pydantic 2.x to 3.x

**Impact**: MEDIUM-HIGH
- **Breaks**: Depends on Pydantic breaking changes
  - Field syntax may change
  - Validation API may change
  - Serialization behavior may change

**Action needed**:
1. Review Pydantic 3.x migration guide
2. Update model definitions to new syntax
3. Update all validators
4. Update serialization code (model_dump, etc.)
5. Run all tests
6. Fix any breaking changes

**Recommendation**: Pin Pydantic version, upgrade carefully with testing

### 🔄 What CAN Be Changed Safely

1. ✅ **Add new fields to models** (as Optional)
   - Impact: None if Optional with default=None
   - Example: `new_field: Optional[str] = None`
   - Backward compatible

2. ✅ **Add new LogicalType enum values**
   - Impact: Additive change
   - Must update Parser and Checker to handle it
   - Backward compatible

3. ✅ **Add new exception types**
   - Impact: None (models don't raise exceptions)
   - Just document them

4. ✅ **Add metadata fields** (using metadata dict)
   - Impact: None (metadata is free-form dict)
   - Safe for extensibility

5. ✅ **Add new Violation types**
   - Impact: None (violation_type is free-form string)
   - Document new types

6. ✅ **Change docstrings**
   - Impact: None on code
   - Improves documentation

### 🚫 What CANNOT Be Changed Without Major Work

1. ❌ **Remove required fields from LogicalForm**
   - Breaks: Everything
   - Effort: CRITICAL

2. ❌ **Change embedding dimension**
   - Breaks: Validation, Encoder, Memory, all stored data
   - Effort: CRITICAL (full system reset)

3. ❌ **Change field types** (e.g., UUID → str)
   - Breaks: Serialization, database storage, comparisons
   - Effort: Very high

4. ❌ **Remove LogicalType or Polarity values**
   - Breaks: Stored data, Parser, Checker
   - Effort: High (requires migration)

5. ❌ **Change normalization logic**
   - Breaks: Comparisons, consistency checks
   - Effort: High (re-normalize all data)

6. ❌ **Change Pydantic to different validation library**
   - Breaks: Everything
   - Effort: CRITICAL

### 📋 Component Dependencies (Post Stage 0.3)

```
glcs/core/models.py (defines)
    ↓
All components import models
    ↓
┌─────────────────┬──────────────────┬─────────────────┬────────────────────┐
│                 │                  │                 │                    │
Logical Parser   Semantic Encoder   Memory Manager   Consistency Checker   API Layer
│                 │                  │                 │                    │
Creates          Adds embedding     Stores           Compares             Returns
LogicalForm      to LogicalForm     LogicalForm      LogicalForm          ConsistencyReport
│                 │                  │                 │                    │
Uses:            Uses:              Uses:             Uses:                Uses:
- Entity         - LogicalForm      - LogicalForm     - LogicalForm        - ConsistencyReport
- Relation       - np.ndarray       - Entity          - Violation          - Violation
- LogicalType                       - Relation        - LogicalType        - LogicalForm
- Polarity                                            - Polarity
```

**Critical Path**:
- models.py → LogicalForm → ALL components
- Changes to LogicalForm cascade to EVERYTHING

### 🎯 Component Contracts (Post Stage 0.3)

**Logical Parser MUST**:
1. Create valid `LogicalForm` objects
2. Set `confidence_score` between 0.0-1.0
3. Populate `source_text` with original input
4. Use correct `LogicalType` enum values
5. Use correct `Polarity` enum values
6. Normalize entities/relations (will happen automatically via Pydantic)

**Semantic Encoder MUST**:
1. Add exactly 768-dimensional `embedding` to LogicalForm
2. Use `sentence-transformers/all-MiniLM-L6-v2` (or compatible model)
3. Never modify other LogicalForm fields
4. Handle Optional embedding (check if None before encoding)

**Memory Manager MUST**:
1. Store complete `LogicalForm` objects
2. Preserve all fields including `form_id`
3. Support queries returning LogicalForm objects
4. Handle 768-dimensional embeddings

**Consistency Checker MUST**:
1. Return valid `ConsistencyReport` objects
2. Create `Violation` objects with minimum 2 conflicting UUIDs
3. Set `is_consistent` correctly (True if no violations)
4. Use valid severity values ("HIGH", "MEDIUM", "LOW")
5. Compare LogicalForms using normalized Entity/Relation values

**API Layer MUST**:
1. Serialize models to JSON using `.model_dump()`
2. Deserialize from JSON using `.model_validate_json()`
3. Return `ConsistencyReport` as final response
4. Handle Pydantic `ValidationError` for invalid inputs

### 🎯 Action Items for Future Stages

**All future components MUST**:
1. Import models from `glcs.core.models`
2. Use exact model structure (don't modify schemas)
3. Use Pydantic validation (don't bypass validators)
4. Follow component contracts above
5. Test with invalid data to verify validation
6. Document which models they use

**Example Component Pattern**:
```python
from glcs.core.models import LogicalForm, Entity, Relation, LogicalType, Polarity

class NewComponent:
    def process(self, text: str, context_id: str) -> LogicalForm:
        # Create models using proper structure
        form = LogicalForm(
            context_id=context_id,
            logical_type=LogicalType.GROUND_FACT,
            subject=Entity(name="example"),
            predicate=Relation(verb="is"),
            polarity=Polarity.POSITIVE,
            source_text=text
        )
        # Pydantic validates automatically
        return form
```

### 📊 Stage 0.3 Impact Summary

**Created Contracts**:
- 7 Pydantic models (Entity, Relation, LogicalType, Polarity, LogicalForm, Violation, ConsistencyReport)
- Embedding dimension: 768 (CRITICAL invariant)
- Confidence score range: 0.0-1.0
- Normalization rules: lowercase + trim
- Validation rules: enforced automatically by Pydantic

**High-Risk Changes**:
- Modifying LogicalForm structure
- Changing embedding dimension
- Removing enum values
- Changing field types
- Modifying normalization logic

**Low-Risk Changes**:
- Adding Optional fields to models
- Adding new LogicalType values
- Adding metadata entries
- Changing docstrings
- Adding new validation for edge cases

**Dependencies Created**:
- ALL components → glcs.core.models
- Parser → Entity, Relation, LogicalType, Polarity, LogicalForm
- Encoder → LogicalForm (reads and modifies)
- Memory → LogicalForm (stores)
- Checker → LogicalForm, Violation, ConsistencyReport

**Test Coverage**: 99% (42 tests, all passing)

### 💡 Migration Strategy for Breaking Changes

If LogicalForm MUST change:

1. **Version the schema**:
   ```python
   class LogicalFormV1(BaseModel): ...
   class LogicalFormV2(BaseModel): ...  # New version
   ```

2. **Create migration function**:
   ```python
   def migrate_v1_to_v2(form_v1: LogicalFormV1) -> LogicalFormV2:
       return LogicalFormV2(
           # Map old fields to new fields
       )
   ```

3. **Support both versions temporarily**:
   - Components accept both v1 and v2
   - Migrate on read

4. **Deprecation period**:
   - Warn when v1 is used
   - Document migration path

5. **Remove old version**:
   - After all data migrated
   - After deprecation period (e.g., 6 months)

---

## Stage 1.1: Semantic Encoder

### ✅ Decisions Made (Fixed)

1. **Model: `all-mpnet-base-v2`**
   - Produces exactly 768-dimensional embeddings
   - Downloaded from HuggingFace on first use (~420MB)
   - **Impact**: All embeddings in the system are from this model
   - **Contract**: Model must always produce 768 dimensions

2. **Embedding Dimension: 768**
   - Enforced by LogicalForm.embedding validator
   - **Impact**: Cannot change without full data migration
   - **Breaking change if altered**: ALL stored LogicalForms become invalid

3. **Normalization: L2 by Default**
   - All embeddings are L2-normalized (unit vectors)
   - Enables fast cosine similarity via dot product
   - **Impact**: Similarity calculations assume normalized vectors
   - **Contract**: `encode()` and `encode_batch()` normalize by default

4. **Singleton Pattern**
   - Model cached at class level
   - Shared across all SemanticEncoder instances
   - **Impact**: First encoding loads model, subsequent are fast
   - **Memory**: ~420MB constant footprint per process

5. **Integration Points**
   - `add_embedding_to_form()`: Adds embedding to single LogicalForm
   - `add_embeddings_to_forms()`: Batch adds embeddings
   - **Contract**: Must accept LogicalForm objects, modify in-place

6. **Dependencies Added**
   - sentence-transformers ^5.1.2
     - Pulls in: PyTorch, transformers, scikit-learn
     - Total size: ~2GB of dependencies
   - **Impact**: Installation is slower, production containers are larger

### 🔗 Component Dependencies

**SemanticEncoder depends on:**
- `glcs.core.models.LogicalForm` (CRITICAL)
  - Reads: `source_text` field
  - Writes: `embedding` field
- `numpy` (CRITICAL)
  - Uses: Arrays for embeddings
- `sentence-transformers` (CRITICAL)
  - Uses: Model loading and encoding

**Components that will depend on SemanticEncoder:**
- **Memory Manager (Stage 1.2)**: Uses embeddings for vector storage
- **Consistency Checker (Stage 1.3)**: Uses `cosine_similarity()` for semantic comparison
- **Logical Parser (Stage 1.4)**: Calls `add_embedding_to_form()` after parsing
- **API Layer (Stage 2.x)**: May expose encoding endpoints

### ⚠️ Potential Cascade Effects

#### If Model Changes (e.g., to different sentence-transformers model)
**Impact**: CRITICAL - Data migration required

**What breaks:**
- Embedding dimensions may change (not 768 anymore)
- LogicalForm validation rejects new embeddings
- Existing embeddings incompatible with new ones
- Cosine similarities between old/new embeddings are meaningless

**Action needed:**
1. **Update LogicalForm validator** to accept new dimension
2. **Re-encode ALL existing LogicalForms**
3. **Update vector database** to new dimension
4. **Recompute all similarities**
5. **Update documentation** with new model name
6. **Test performance** (speed and accuracy may differ)

**Recommendation**: Only change model if absolutely necessary. Treat as major version bump.

#### If Embedding Dimension Changes
**Impact**: CRITICAL - Breaking change

**What breaks:**
- LogicalForm.embedding validation fails
- Vector database schema incompatible
- Memory Manager storage layer breaks
- All existing stored forms invalid

**Action needed:**
- This is a **breaking change** requiring full data wipe or migration
- See "Migration Path for Breaking Changes" section

#### If L2 Normalization is Removed
**Impact**: HIGH - Breaks similarity calculations

**What breaks:**
- `cosine_similarity()` formula assumes normalized vectors
- Dot product ≠ cosine similarity anymore
- Consistency Checker results wrong
- Need to use full cosine formula: `dot(a,b) / (norm(a) * norm(b))`

**Action needed:**
1. **Update `cosine_similarity()` method** to compute norms
2. **Update vector database queries** (if using dot product)
3. **Retest all similarity thresholds** (values may change)
4. **Performance may degrade** (~2x slower similarity)

**Recommendation**: Keep normalization. It's a standard practice.

#### If `add_embedding_to_form()` Signature Changes
**Impact**: MEDIUM - Breaks dependent components

**Current signature:**
```python
def add_embedding_to_form(form: LogicalForm) -> LogicalForm
```

**If changed to** (example):
```python
def add_embedding_to_form(form: LogicalForm, model_name: str = "all-mpnet-base-v2") -> LogicalForm
```

**What breaks:**
- Logical Parser calls (Stage 1.4)
- API endpoints that use this method
- Integration tests

**Action needed:**
- Make new parameters **optional** (backward compatible)
- Deprecate old signature gradually
- Update all call sites

#### If Model Caching is Removed
**Impact**: LOW - Performance only

**What breaks:**
- Nothing functionally
- Each SemanticEncoder instance loads 420MB model
- Memory usage increases (N encoders = N × 420MB)
- Initialization slower (~5 seconds per encoder)

**Recommendation**: Keep caching. No good reason to remove it.

### 📊 Contracts Established

#### Contract 1: Embedding Dimension = 768
**Enforced by:** LogicalForm validator
**Used by:** Memory Manager, Consistency Checker
**Breaking change if violated:** Yes

**Test verification:**
```python
# tests/unit/test_semantic_encoder.py::test_embedding_dimension_exactly_768
# tests/unit/test_models.py::test_logical_form_with_valid_embedding
```

#### Contract 2: Model Returns Deterministic Results
**Enforced by:** sentence-transformers library
**Used by:** All components (for consistency)
**Breaking change if violated:** Moderate

**Test verification:**
```python
# tests/unit/test_semantic_encoder.py::test_encode_is_deterministic
```

#### Contract 3: Cosine Similarity Range [-1, 1]
**Enforced by:** Mathematics, L2 normalization
**Used by:** Consistency Checker
**Breaking change if violated:** Yes

**Test verification:**
```python
# tests/unit/test_semantic_encoder.py::test_cosine_similarity_range
```

#### Contract 4: Model Singleton Pattern
**Enforced by:** Class-level `_model_cache`
**Used by:** All SemanticEncoder instances
**Breaking change if violated:** No (performance only)

**Test verification:**
```python
# tests/unit/test_semantic_encoder.py::test_model_cache_reuses_model
```

#### Contract 5: Empty Text Rejection
**Enforced by:** `encode()` validation
**Used by:** All encoding operations
**Breaking change if violated:** Moderate

**Test verification:**
```python
# tests/unit/test_semantic_encoder.py::test_encode_empty_text_raises_error
```

### 🚨 High-Risk Changes

**NEVER change these without full team review:**
1. **Embedding dimension** (768) - CRITICAL
2. **Model name** (all-mpnet-base-v2) - CRITICAL
3. **Normalization** (L2) - HIGH
4. **Method signatures** (`add_embedding_to_form`) - MEDIUM

**Low-risk changes (safe to modify):**
1. Model caching implementation
2. Error messages
3. Internal helper methods
4. Docstrings

### 🔄 Integration with Previous Stages

**Stage 0.3 (Data Models) → Stage 1.1 (Semantic Encoder)**

**Changes to Stage 0.3:**
- ✅ Added `validate_assignment=True` to LogicalForm.model_config
  - **Why**: Needed for embedding validation on field assignment
  - **Impact**: LOW - More validation is good
  - **Breaking**: No - Backward compatible

**Python Version Change:**
- ✅ Changed `python = "^3.11"` to `python = "^3.10"`
- ✅ Changed `numpy = "^2.3.4"` to `numpy = "^1.26.0"`
  - **Why**: User environment had Python 3.10.10
  - **Impact**: LOW - NumPy 1.26 supports all our use cases
  - **Breaking**: No - Only affects new installations

---

## Stage Completion Status

- ✅ **Stage 0.1**: Complete
  - Dependencies: Poetry, Python 3.10+, package structure
  - Contracts: Import paths, package name
  - Risk: Changing these is HIGH impact

- ✅ **Stage 0.2**: Complete
  - Dependencies: PyYAML, config schema, exception hierarchy
  - Contracts: Config file structure, logger usage pattern, exception types
  - Risk: Config schema changes are HIGH impact, exceptions are MEDIUM impact

- ✅ **Stage 0.3**: Complete
  - Dependencies: Pydantic, numpy, sentence-transformers
  - Contracts: Data model schemas (LogicalForm, etc.), 768-dim embeddings, validation rules
  - Risk: Model schema changes are CRITICAL impact
  - Test Coverage: 99% (42 tests passing)

- ✅ **Stage 1.1**: Complete
  - Dependencies: sentence-transformers (all-mpnet-base-v2), PyTorch
  - Contracts: 768-dim embeddings, L2 normalization, model singleton, method signatures
  - Risk: Model/dimension changes are CRITICAL, normalization changes HIGH
  - Test Coverage: 97% (32 tests passing)
  - Overall Coverage: 91% (111 tests total)

---

## Notes for Future Developers

1. **Import paths are sacred**: Once established, very hard to change
2. **Config schema is a contract**: Version it if you change it
3. **Data models are contracts**: Use migrations for schema changes
4. **Embedding dimension is fixed**: Don't change without full system reset
5. **Test for cascade effects**: When changing core components, run FULL test suite
6. **Document breaking changes**: Keep CHANGELOG.md updated
7. **LogicalForm is the heart**: ALL components depend on it - changes cascade everywhere
8. **Model choice is permanent**: Changing sentence-transformers model = data migration
9. **Normalization matters**: L2 normalization enables fast similarity calculations

---

## Stage 1.2: Memory Manager - Cascade Analysis

### ✅ Decisions Made (Fixed Contracts)

1. **Vector Database: ChromaDB**
   - Embedded database (no external service required)
   - In-memory mode for testing, persistent for production
   - Built-in similarity search with metadata filtering
   - **Impact**: All vector storage uses ChromaDB API
   - **Contract**: CRUD operations + semantic search interface
   - **Dependency Added**: chromadb ^0.5.20 (~65 additional packages)

2. **Dual-Mode Operation**
   ```python
   # In-memory (testing)
   MemoryManager(collection_name="test", in_memory=True)

   # Persistent (production)
   MemoryManager(collection_name="forms", persist_directory="./chroma_db")
   ```
   - **Impact**: Tests use in-memory, production uses persistent
   - **Contract**: Both modes have identical API

3. **Storage Schema**
   - **Embeddings**: 768-dimensional vectors (from SemanticEncoder)
   - **Metadata**: Indexed fields for filtering
     - `context_id`, `logical_type`, `polarity`
     - `subject_name`, `predicate_verb`, `object_name`
     - `confidence_score`, `timestamp`
   - **Documents**: Original `source_text`
   - **Impact**: Enables fast filtering + semantic search
   - **Contract**: Cannot change metadata structure without migration

4. **Required Embedding on Storage**
   - `store_form()` requires LogicalForm.embedding to be set
   - Raises `GLCSMemoryError` if embedding is None
   - **Impact**: Forces SemanticEncoder usage before storage
   - **Contract**: Enforces proper pipeline order

5. **Context-Based Organization**
   - All queries can filter by `context_id`
   - Contexts are logical groupings (sessions/conversations)
   - **Impact**: Enables multi-session isolation
   - **Contract**: context_id is primary organizational unit

6. **Entity/Relation Normalization Matching**
   - Stores normalized forms (lowercase, trimmed)
   - Matches LogicalForm normalization from Stage 0.3
   - **Impact**: Consistent search behavior
   - **Contract**: Search queries automatically normalized

### 🔗 Component Dependencies

**MemoryManager depends on:**
- `glcs.core.models.LogicalForm` (CRITICAL)
  - Reads: All fields for storage
  - Validates: embedding is present
- `chromadb` (CRITICAL)
  - Uses: Collection operations, similarity search
- `glcs.core.semantic_encoder.SemanticEncoder` (for integration)
  - Uses: Must be called before storage
- `numpy` (CRITICAL)
  - Uses: Embedding array operations

**Components that depend on MemoryManager:**
- **Consistency Checker (Stage 1.3)**: Calls `get_forms_by_context()` to retrieve forms for checking
- **Logical Parser (Stage 1.4)**: Stores parsed forms via `store_form()`
- **API Layer (Stage 2.x)**: Exposes storage/retrieval endpoints

### ⚠️ Potential Cascade Effects

#### If ChromaDB is Replaced (e.g., with FAISS/Pinecone)
**Impact**: HIGH - Major refactoring required

**What breaks:**
- All ChromaDB-specific API calls
- Collection management code
- Metadata filtering logic (different API)
- In-memory mode implementation

**Action needed:**
1. **Create abstraction layer** for vector DB operations
2. **Implement new backend** with same interface
3. **Migrate stored data** to new format
4. **Update tests** for new backend
5. **Update configuration** with new DB settings
6. **Performance testing** (may differ significantly)

**Recommendation**: Stick with ChromaDB unless strong reason to change

#### If Storage Metadata Schema Changes
**Impact**: MEDIUM-HIGH - Requires data migration

**Example**: Add new metadata field `parser_version`

**What breaks:**
- Existing stored forms lack new field
- Queries filtering on new field return no results
- Reconstruction logic expects new field

**Action needed:**
1. **Update `store_form()` method** to include new metadata
2. **Migrate existing data** (add default values)
3. **Update query methods** to handle new field
4. **Update tests** with new metadata
5. **Update documentation**

**Recommendation**: Add new metadata as optional, backfill later

#### If Embedding Requirement is Removed
**Impact**: HIGH - Breaks consistency checking

**Scenario**: Allow storing forms without embeddings

**What breaks:**
- `search_similar_forms()` fails (no embedding to compare)
- Consistency Checker semantic similarity checks fail
- Vector search becomes impossible

**Action needed:**
- DON'T remove this requirement
- Embeddings are core to GLCS semantic capabilities

**Recommendation**: Keep embedding requirement mandatory

#### If Context Organization Changes
**Impact**: MEDIUM - Affects all context-based queries

**Scenario**: Add hierarchical contexts (e.g., `session.conversation.turn`)

**What breaks:**
- Current flat context_id structure
- `get_forms_by_context()` returns too many results
- `list_contexts()` format changes

**Action needed:**
1. **Update context_id format** (e.g., dot-separated)
2. **Add context hierarchy parsing**
3. **Update query methods** to support hierarchy
4. **Migrate existing context IDs**
5. **Update tests**

**Recommendation**: Keep flat structure for now, add hierarchy later if needed

#### If CRUD Methods Change Signatures
**Impact**: MEDIUM - Breaks dependent code

**Current signatures:**
```python
def store_form(form: LogicalForm) -> UUID
def retrieve_form(form_id: UUID) -> LogicalForm
def update_form(form: LogicalForm) -> UUID
def delete_form(form_id: UUID) -> bool
```

**If changed** (example: add version tracking):
```python
def store_form(form: LogicalForm, version: int = 1) -> UUID
```

**What breaks:**
- Parser calls to `store_form()`
- API endpoints
- Integration tests

**Action needed:**
- Make new parameters **optional** with defaults
- Update all call sites gradually
- Deprecate old signature if needed

### 📊 Contracts Established

#### Contract 1: Embedding Required for Storage
**Enforced by:** `store_form()` validation
**Used by:** Consistency Checker, semantic search
**Breaking change if violated:** Yes

**Test verification:**
```python
# tests/unit/test_memory_manager.py::test_store_form_without_embedding_raises_error
```

#### Contract 2: CRUD Operations Return Specific Types
**Enforced by:** Type hints and implementation
**Used by:** All components storing/retrieving forms
**Breaking change if violated:** Yes

**Signatures:**
- `store_form()` → UUID
- `retrieve_form()` → LogicalForm
- `update_form()` → UUID
- `delete_form()` → bool

#### Contract 3: Context Isolation
**Enforced by:** Metadata filtering in ChromaDB
**Used by:** Multi-session applications
**Breaking change if violated:** Moderate

**Test verification:**
```python
# tests/unit/test_memory_manager.py::test_get_forms_by_context_isolation
```

#### Contract 4: Semantic Search Returns Ranked Results
**Enforced by:** ChromaDB similarity scoring
**Used by:** Consistency Checker, future retrieval features
**Breaking change if violated:** Moderate

**Contract:**
- Returns up to `top_k` results
- Results sorted by similarity (highest first)
- Can filter by context_id

### 🚨 High-Risk Changes

**NEVER change these without full team review:**
1. **Vector database choice** (ChromaDB) - HIGH
2. **Embedding requirement** (mandatory) - CRITICAL
3. **Metadata schema** (structure) - MEDIUM-HIGH
4. **CRUD method signatures** - MEDIUM
5. **Context_id structure** (flat string) - MEDIUM

**Low-risk changes (safe to modify):**
1. Default collection names
2. Persist directory paths
3. Error messages
4. Internal helper methods
5. Statistics computation logic

### 🔄 Integration with Previous Stages

**Integrates with:**

**Stage 0.3 (Data Models):**
- Uses `LogicalForm`, `Entity`, `Relation`
- Enforces embedding validation
- Relies on normalized entity/relation names

**Stage 1.1 (Semantic Encoder):**
- Requires forms to have embeddings before storage
- Uses 768-dimensional embeddings
- Pipeline: Encode → Store

**Stage 0.2 (Configuration):**
- Could use config for persist_directory (future enhancement)
- Exception hierarchy: raises `GLCSMemoryError`

### 📋 Test Coverage

**Test File:** `tests/unit/test_memory_manager.py`
**Coverage:** 84% (161/190 lines)
**Tests:** 29 tests, all passing

**Uncovered lines:** Exception paths (form not found, empty contexts, etc.)

---

## Stage 1.3: Consistency Checker - Cascade Analysis

### ✅ Decisions Made (Fixed Contracts)

1. **Violation Types (4 types)**
   - **POLARITY_CONTRADICTION**: Opposite polarities + high similarity (≥ 0.8)
   - **UNIVERSAL_GROUND_CONTRADICTION**: Ground fact violating universal rule
   - **EXACT_REDUNDANCY**: Identical source text (case-insensitive)
   - **SEMANTIC_REDUNDANCY**: High similarity + same polarity (≥ redundancy_threshold)
   - **Impact**: Future code may expect these specific types
   - **Contract**: Violation.violation_type uses these exact strings

2. **Similarity Thresholds**
   - **Contradiction detection**: 0.8 (hardcoded in code)
   - **Redundancy detection**: 0.9 (configurable via init parameter)
   - **Impact**: Affects sensitivity of detection
   - **Contract**: Thresholds are numeric, not in config (for now)

3. **Severity Levels (3 levels)**
   - **HIGH**: Universal rule violations, high-confidence contradictions (avg ≥ 0.9)
   - **MEDIUM**: Medium-confidence contradictions (avg ≥ 0.7)
   - **LOW**: Redundancies, low-confidence contradictions
   - **Impact**: API consumers may filter by severity
   - **Contract**: Severity must be exactly "HIGH", "MEDIUM", or "LOW"

4. **Consistency Checking Strategy**
   - **Pairwise comparison**: O(n²) complexity
   - **Structural similarity first**: Fast filter (same subject/predicate/object)
   - **Semantic similarity second**: Slower (embedding comparison)
   - **Impact**: Performance degrades with many forms in context
   - **Contract**: All forms are compared exhaustively

5. **Two Check Methods**
   ```python
   # Check entire context
   check_context_consistency(context_id: str) -> ConsistencyReport

   # Check new form against context
   check_form_against_context(form: LogicalForm, context_id: str) -> ConsistencyReport
   ```
   - **Impact**: Two different use cases (audit vs. pre-validation)
   - **Contract**: Both return ConsistencyReport with same structure

6. **Integration with MemoryManager**
   - Calls `memory.get_forms_by_context(context_id)`
   - Depends on MemoryManager retrieval accuracy
   - **Impact**: Consistency checking limited to what's in memory
   - **Contract**: MemoryManager is source of truth

### 🔗 Component Dependencies

**ConsistencyChecker depends on:**
- `glcs.core.models` (CRITICAL)
  - Uses: `LogicalForm`, `Violation`, `ConsistencyReport`, `LogicalType`, `Polarity`
  - Creates: Violation and ConsistencyReport objects
- `glcs.core.memory_manager.MemoryManager` (CRITICAL)
  - Calls: `get_forms_by_context()`
  - Depends on: Accurate retrieval of all forms in context
- `glcs.core.semantic_encoder.SemanticEncoder` (CRITICAL)
  - Calls: `cosine_similarity(emb1, emb2)`
  - Depends on: L2-normalized embeddings

**Components that will depend on ConsistencyChecker:**
- **API Layer (Stage 2.x)**: Exposes consistency checking endpoints
- **Logical Parser (Stage 1.4)**: May call `check_form_against_context()` before storing
- **Future UI**: Displays violations to users

### ⚠️ Potential Cascade Effects

#### If Similarity Thresholds Change
**Impact**: MEDIUM - Changes detection sensitivity

**Scenario**: Change contradiction threshold from 0.8 to 0.7

**What breaks:**
- Nothing (backward compatible)
- **Affects behavior**:
  - More contradictions detected (more false positives)
  - May overwhelm users with violations

**Action needed:**
1. **Move thresholds to config** (future enhancement)
2. **Test new threshold** on sample data
3. **Document threshold** in user guide
4. **Update tests** with new expected results

**Recommendation**: Make thresholds configurable via init parameters

#### If New Violation Types Added
**Impact**: LOW - Additive change

**Example**: Add `TEMPORAL_CONTRADICTION` (conflicting time claims)

**What breaks:**
- Nothing (backward compatible)

**Action needed:**
1. **Add detection logic** in new method
2. **Call new method** from `check_context_consistency()`
3. **Add tests** for new violation type
4. **Update documentation**
5. **Update `get_violation_summary()` if needed**

**Recommendation**: Easy to add, document well

#### If Severity Calculation Changes
**Impact**: MEDIUM - Changes violation priority

**Scenario**: Make all polarity contradictions HIGH (ignore confidence)

**What breaks:**
- Existing violations may have different severity
- API consumers filtering by severity affected
- User workflows expecting current severities

**Action needed:**
1. **Update `_calculate_severity()` method**
2. **Re-check all stored violations** (if cached)
3. **Update documentation**
4. **Inform users** of severity changes

**Recommendation**: Document severity logic clearly, change carefully

#### If Consistency Checking Algorithm Changes
**Impact**: MEDIUM-HIGH - May find different violations

**Scenario**: Use semantic similarity only (remove structural check)

**What breaks:**
- May find more contradictions (performance impact)
- Different forms flagged as violations
- Tests expecting specific violations may fail

**Action needed:**
1. **Benchmark performance** (O(n²) semantic checks expensive)
2. **Test on sample data** (precision/recall changes)
3. **Update tests** with new expected results
4. **Document algorithm** changes

**Recommendation**: Keep hybrid approach (structural + semantic)

#### If MemoryManager API Changes
**Impact**: HIGH - Breaks integration

**Scenario**: `get_forms_by_context()` signature changes

**What breaks:**
- ConsistencyChecker can't retrieve forms
- `check_context_consistency()` fails

**Action needed:**
1. **Update ConsistencyChecker** to use new API
2. **Update tests**
3. **Coordinate changes** with MemoryManager stage

**Recommendation**: Keep MemoryManager API stable

#### If ConsistencyReport Structure Changes
**Impact**: HIGH - Breaks API consumers

**Scenario**: Add new field `recommendations: List[str]`

**What breaks:**
- API consumers expecting old structure
- Serialization/deserialization may fail
- Tests expecting specific fields

**Action needed:**
1. **Make new field optional** (backward compatible)
2. **Update API documentation**
3. **Version API** if breaking change
4. **Update tests**

**Recommendation**: Add optional fields only, version breaking changes

### 📊 Contracts Established

#### Contract 1: Four Violation Types
**Enforced by:** Implementation logic
**Used by:** API consumers, violation summaries
**Breaking change if violated:** No (can add more)

**Types:**
- POLARITY_CONTRADICTION
- UNIVERSAL_GROUND_CONTRADICTION
- EXACT_REDUNDANCY
- SEMANTIC_REDUNDANCY

#### Contract 2: Three Severity Levels
**Enforced by:** `_calculate_severity()` method, Violation model validation
**Used by:** API consumers, filtering logic
**Breaking change if violated:** Yes (Violation model enforces)

**Levels:** "HIGH", "MEDIUM", "LOW"

#### Contract 3: ConsistencyReport Format
**Enforced by:** Pydantic ConsistencyReport model
**Used by:** API responses, violation display
**Breaking change if violated:** Yes

**Fields:**
- `report_id`, `context_id`, `is_consistent`
- `violations: List[Violation]`
- `total_forms_checked`, `generated_at`, `metadata`

#### Contract 4: Pairwise Exhaustive Checking
**Enforced by:** Implementation (nested loops)
**Used by:** Consistency guarantees
**Breaking change if violated:** Moderate

**Guarantee:** All pairs of forms are compared (no violations missed)

#### Contract 5: Empty Context is Consistent
**Enforced by:** `check_context_consistency()` logic
**Used by:** API consumers
**Breaking change if violated:** Moderate

**Behavior:** Returns `is_consistent=True` with `violations=[]`

### 🚨 High-Risk Changes

**NEVER change these without full team review:**
1. **Violation types** (removal) - MEDIUM
2. **Severity levels** (values) - HIGH (Violation model enforces)
3. **ConsistencyReport structure** (required fields) - HIGH
4. **Method signatures** (`check_context_consistency`, `check_form_against_context`) - MEDIUM
5. **Exhaustive checking guarantee** - MEDIUM

**Low-risk changes (safe to modify):**
1. Similarity thresholds (make configurable)
2. Add new violation types (additive)
3. Add optional fields to ConsistencyReport
4. Improve algorithm efficiency (same results)
5. Error messages and explanations

### 🔄 Integration with Previous Stages

**Integrates with:**

**Stage 0.3 (Data Models):**
- Creates `Violation` and `ConsistencyReport` objects
- Uses `LogicalType` and `Polarity` enums
- Relies on `LogicalForm` structure

**Stage 1.1 (Semantic Encoder):**
- Calls `encoder.cosine_similarity(emb1, emb2)`
- Depends on L2-normalized embeddings
- Uses 768-dimensional vectors

**Stage 1.2 (Memory Manager):**
- Calls `memory.get_forms_by_context(context_id)`
- Depends on accurate form retrieval
- Assumes embeddings are present

**Stage 0.2 (Exceptions):**
- Raises `ConsistencyError` on failures
- Follows exception hierarchy

### 📋 Test Coverage

**Test File:** `tests/unit/test_consistency_checker.py`
**Coverage:** 86% (149/170 lines)
**Tests:** 18 tests, all passing

**Test Categories:**
- Initialization (3 tests)
- Polarity contradiction detection (2 tests)
- Universal vs ground contradiction (2 tests)
- Redundancy detection (2 tests)
- Context consistency checking (3 tests)
- Form vs context checking (2 tests)
- Severity scoring (2 tests)
- Violation summary (1 test)
- Full integration workflow (1 test)

**Uncovered lines:** Exception paths, edge cases in severity calculation

### 📊 Performance Considerations

**Complexity:** O(n²) where n = number of forms in context

**Bottlenecks:**
- Semantic similarity calculations (costly)
- Large contexts (100+ forms) may be slow

**Optimization opportunities:**
1. Cache similarity calculations
2. Use structural filtering more aggressively
3. Implement sampling for very large contexts
4. Parallelize pairwise comparisons

**Recommendation:** Monitor performance, optimize if needed in future

---

## Stage Completion Status

- ✅ **Stage 0.1**: Complete
  - Dependencies: Poetry, Python 3.10+, package structure
  - Contracts: Import paths, package name
  - Risk: Changing these is HIGH impact

- ✅ **Stage 0.2**: Complete
  - Dependencies: PyYAML, config schema, exception hierarchy
  - Contracts: Config file structure, logger usage pattern, exception types
  - Risk: Config schema changes are HIGH impact, exceptions are MEDIUM impact

- ✅ **Stage 0.3**: Complete
  - Dependencies: Pydantic, numpy, sentence-transformers
  - Contracts: Data model schemas (LogicalForm, etc.), 768-dim embeddings, validation rules
  - Risk: Model schema changes are CRITICAL impact
  - Test Coverage: 99% (42 tests passing)

- ✅ **Stage 1.1**: Complete
  - Dependencies: sentence-transformers (all-mpnet-base-v2), PyTorch
  - Contracts: 768-dim embeddings, L2 normalization, model singleton, method signatures
  - Risk: Model/dimension changes are CRITICAL, normalization changes HIGH
  - Test Coverage: 97% (32 tests passing)

- ✅ **Stage 1.2**: Complete
  - Dependencies: ChromaDB (vector database)
  - Contracts: CRUD operations, embedding requirement, context isolation, metadata schema
  - Risk: Database changes HIGH, metadata schema MEDIUM-HIGH, embedding requirement CRITICAL
  - Test Coverage: 84% (29 tests passing)

- ✅ **Stage 1.3**: Complete
  - Dependencies: MemoryManager, SemanticEncoder, data models
  - Contracts: Violation types, severity levels, ConsistencyReport structure, exhaustive checking
  - Risk: Report structure HIGH, severity levels HIGH, violation types MEDIUM
  - Test Coverage: 86% (18 tests passing)
  - Overall Coverage: 88% (165 tests total)

---

## Dependency Graph (Updated)

```
pyproject.toml
    ↓
Poetry install
    ↓
Dependencies: Pydantic, numpy, sentence-transformers, chromadb
    ↓
glcs.core.models (Stage 0.3)
    ↓
    ├─→ glcs.core.semantic_encoder (Stage 1.1)
    │       ↓
    │   Adds embeddings to LogicalForm
    │       ↓
    ├─→ glcs.core.memory_manager (Stage 1.2)
    │       ↓
    │   Stores LogicalForm in ChromaDB
    │       ↓
    └─→ glcs.core.consistency_checker (Stage 1.3)
            ↓
        Retrieves forms from MemoryManager
        Uses SemanticEncoder for similarity
        Creates ConsistencyReport with Violations
```

**Critical Dependencies:**
1. LogicalForm → ALL components (CRITICAL)
2. SemanticEncoder → MemoryManager, ConsistencyChecker
3. MemoryManager → ConsistencyChecker
4. 768-dim embeddings → Encoder, Memory, Checker

---

## Notes for Future Developers

1. **Import paths are sacred**: Once established, very hard to change
2. **Config schema is a contract**: Version it if you change it
3. **Data models are contracts**: Use migrations for schema changes
4. **Embedding dimension is fixed**: Don't change without full system reset
5. **Test for cascade effects**: When changing core components, run FULL test suite
6. **Document breaking changes**: Keep CHANGELOG.md updated
7. **LogicalForm is the heart**: ALL components depend on it - changes cascade everywhere
8. **Model choice is permanent**: Changing sentence-transformers model = data migration
9. **Normalization matters**: L2 normalization enables fast similarity calculations
10. **ChromaDB is embedded**: No external service, dual-mode (in-memory + persistent)
11. **Embedding is mandatory**: Cannot store forms without embeddings
12. **Context isolation**: All operations respect context boundaries
13. **Consistency checking is exhaustive**: O(n²) pairwise comparison
14. **Violations have fixed types**: Adding is OK, removing requires migration

---

**Last Review**: Stage 1.3 completion
**Next Review**: After Stage 1.4 (Logical Parser)
