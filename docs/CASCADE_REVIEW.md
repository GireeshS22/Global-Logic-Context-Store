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

**Last Review**: Stage 0.2 completion
**Next Review**: After Stage 0.3 (Data Models)
