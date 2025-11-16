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

- ⏳ **Stage 0.2**: Not started
- ⏳ **Stage 0.3**: Not started

---

## Notes for Future Developers

1. **Import paths are sacred**: Once established, very hard to change
2. **Config schema is a contract**: Version it if you change it
3. **Data models are contracts**: Use migrations for schema changes
4. **Test for cascade effects**: When changing core components, run FULL test suite
5. **Document breaking changes**: Keep CHANGELOG.md updated

---

**Last Review**: Stage 0.1 completion
**Next Review**: After Stage 0.2 (Configuration System)
