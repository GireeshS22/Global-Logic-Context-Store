# GLCS Project Audit — Issues & Fix List

**Project:** Global Logical Context Store (GLCS)
**Audit Date:** 2026-03-05
**Status:** Pre-collaborator onboarding cleanup

---

## Component Audit Status

Carried forward from original audit. Tracks which components have been verified.

| Phase | Stage | Component | Status | Notes |
|-------|-------|-----------|--------|-------|
| Phase 0 | 0.1 | Project Structure | Audited | 15/15 steps complete |
| Phase 0 | 0.2 | Configuration Files | Audited | Using Poetry approach |
| Phase 0 | 0.3 | Data Models (`models.py`) | Audited | 42 tests, serialization issues found (see #14, #15) |
| Phase 0 | 0.4 | Config & Utilities | Audited | 37 tests passing |
| Phase 1 | 1.1 | Semantic Encoder | Audited | 32 tests, thread-safety and doc issues found (see #32, #33) |
| Phase 1 | 1.2 | Memory Manager | Audited | 29 tests, lossy storage found (see #41) |
| Phase 1 | 1.3 | Consistency Checker | Audited | 18 tests, logic flaws found (see #21, #22) |
| Phase 1 | 1.4 | LLM Logical Parser | Audited | 34/35 tests pass, cache bug found (see #11) |
| Phase 1 | 1.5 | AdvancedGLCS Orchestrator | Audited | 9/14 tests pass, API mismatches (see #66, #67, #68) |
| Phase 1 | 1.6 | Examples & Manual Testing | Audited | 5 demo scripts working |
| Phase 2 | 2.1 | REST API | Audited | Multiple runtime crash bugs found (see #4, #5, #6) |
| Phase 2 | 2.2 | WebSocket | Not started | Pending implementation |

---

## TIER 1: CRITICAL — Fix Before Collaborator Pulls

### 1.1 Test Suite Crashers

| # | Issue | File | Details |
|---|-------|------|---------|
| 1 | ~~Raw script crashes entire test suite~~ | ~~`tests/unit/test_providers/test_ollama.py`~~ | **FIXED** Moved to `examples/ollama_wrapper_demo.py`. |
| 2 | ~~Raw script in test directory~~ | ~~`tests/unit/gs_unittest.py`~~ | **FIXED** Moved to `examples/parser_manual_test.py`. |
| 3 | ~~Raw script in test directory~~ | ~~`tests/unit/test_full_pipeline.py`~~ | **FIXED** Moved to `examples/full_pipeline_demo.py`. |

### 1.2 API Endpoints That Crash at Runtime

| # | Issue | File | Details |
|---|-------|------|---------|
| 4 | ~~`/search` endpoint crashes~~ | ~~`glcs/api/routes.py:300-308`~~ | **FIXED** `for form in results` — `search_similar()` returns `List[LogicalForm]`, not tuples. |
| 5 | ~~`/contexts` endpoint crashes~~ | ~~`glcs/api/routes.py:350`~~ | **FIXED** Changed to `glcs.memory.list_contexts()` which exists on `MemoryManager`. |
| 6 | ~~`/check` endpoint mutates state~~ | ~~`glcs/api/routes.py:234`~~ | **FIXED** Now passes `auto_store=False` to `process_statement`. |
| 7 | ~~CORS misconfiguration~~ | ~~`glcs/api/app.py:144-150`~~ | **FIXED** `allow_credentials` now only `True` when `GLCS_CORS_ORIGINS` env var specifies explicit origins. |

### 1.3 Repository Hygiene

| # | Issue | Details |
|---|-------|---------|
| 8 | ~~Delete `nul` file~~ | **FIXED** Deleted from repo root. |
| 9 | ~~Fix `.gitignore` — missing entries~~ | **FIXED** Added `chroma_db/`, `/*.json`, `data/*.jsonl`, `.streamlit/`. |
| 10 | ~~Track `poetry.lock`~~ | **FIXED** Removed `poetry.lock` from `.gitignore`. Now tracked for reproducible builds. |

---

## TIER 2: DATA INTEGRITY — Fix This Week

### 2.1 Active Data Corruption Bugs

| # | Issue | File | Details |
|---|-------|------|---------|
| 11 | ~~Cache mutation bug~~ | ~~`glcs/core/logical_parser.py:239`~~ | **FIXED** Returns `copy.deepcopy()` on cache hit — callers cannot mutate the cached object. |
| 12 | ~~Cache key ignores provider/model~~ | ~~`glcs/core/logical_parser.py:190`~~ | **FIXED** Cache key now hashes `provider:model:temperature:text`. |
| 13 | ~~Unbounded in-memory cache~~ | ~~`glcs/core/logical_parser.py:149`~~ | **FIXED** Replaced `Dict` with `OrderedDict` + LRU eviction, capped at `cache_max_size=1000`. |

### 2.2 Broken Serialization

| # | Issue | File | Details |
|---|-------|------|---------|
| 14 | ~~`model_dump()` round-trip broken~~ | ~~`glcs/core/models.py:222-229`~~ | **FIXED** `mode='before'` validator accepts list and converts back to `np.ndarray`. Round-trip works. |
| 15 | ~~`model_dump_json()` crashes~~ | ~~`glcs/core/models.py`~~ | **FIXED** `@field_serializer('embedding')` converts `np.ndarray` to list on all serialization paths. |
| 16 | ~~`ErrorResponse.model_dump()` crashes~~ | ~~`glcs/api/app.py:190`~~ | **FIXED** Global exception handler now uses `model_dump(mode='json')` — `datetime` serialises to ISO string. |

### 2.3 Naming & Shadowing

| # | Issue | File | Details |
|---|-------|------|---------|
| 17 | ~~`MemoryError` shadows Python builtin~~ | ~~`glcs/utils/exceptions.py:80`~~ | **FIXED** Renamed to `GLCSMemoryError`. Updated all imports in `memory_manager.py`, `advanced_wrapper.py`, `test_exceptions.py`, `test_memory_manager.py`. |
| 18 | ~~Dual `ConsistencyChecker` name collision~~ | ~~`glcs/__init__.py:10` vs `glcs/core/consistency_checker.py`~~ | **FIXED** Simple class renamed to `SimpleConsistencyChecker` in `glcs/checker.py`. Updated `__init__.py`, `llm_wrapper.py`, 3 examples, and 2 test files. Advanced `ConsistencyChecker` in `glcs/core/` unchanged. |

### 2.4 Configuration Mismatch

| # | Issue | File | Details |
|---|-------|------|---------|
| 19 | ~~Model/dimension mismatch~~ | ~~`config/glcs_config.yaml`~~ | **FIXED** Config model changed to `all-mpnet-base-v2` (768-dim). `embedding_dim` now derived from `model.get_sentence_embedding_dimension()` — no longer hardcoded. |
| 20 | ~~`datetime.utcnow()` deprecated~~ | ~~`models.py`, `logical_parser.py`, `app.py`, `routes.py`~~ | **FIXED** All 10 occurrences replaced with `datetime.now(timezone.utc)`. `timezone` added to imports in all 4 files. |

---

## TIER 3: ENGINEERING QUALITY — Fix Before PyPI Release

### 3.1 Consistency Checker Logic

| # | Issue | File | Details |
|---|-------|------|---------|
| 21 | ~~Universal-ground check is logically broken~~ | ~~`consistency_checker.py:396-424`~~ | **FIXED** Added predicate verb check (with copula normalization so "are"/"is" are equivalent), fixed object/unary-predicate handling, and added subject class membership check via exact name match or `entity_type`. Updated 2 tests that used mismatched predicates without `entity_type`. |
| 22 | ~~Polarity check is trivially narrow~~ | ~~`consistency_checker.py:286-320`~~ | **FIXED** Replaced `_are_structurally_similar` gate with subject-name-only match. Embedding similarity (≥0.8) now acts as the sole semantic discriminator, catching paraphrase contradictions. Added 2 regression tests. |
| 23 | ~~O(n^2) pairwise comparisons~~ | ~~`consistency_checker.py:263-268, 447-452`~~ | **FIXED** `_check_polarity_contradictions`: groups by subject then does one `pos @ neg.T` matrix multiply per group. `_check_redundancies`: exact duplicates via O(n) dict grouping; semantic duplicates via matrix @ matrix.T. `_check_universal_ground_contradictions`: groups rules/facts by (predicate, object). `check_form_against_context`: uses targeted memory searches (subject, similar, rules) instead of O(n) scan. |

### 3.2 Provider System

| # | Issue | Files | Details |
|---|-------|-------|---------|
| 24 | ~~String-based error classification~~ | ~~All 5 providers~~ | **FIXED** All providers import typed SDK exceptions with `isinstance` checks; string matching is the fallback only. |
| 25 | ~~Factory crashes on re-import~~ | ~~`glcs/providers/factory.py:28-29`~~ | **FIXED** `register()` is idempotent — same class re-registration is a no-op; different class still raises `ValueError`. |
| 26 | ~~Ollama auto-pulls models without consent~~ | ~~`glcs/providers/ollama_provider.py:92-103`~~ | **FIXED** `auto_pull=False` by default in `config.extra`; missing model raises `ProviderError` with manual pull instructions. |
| 27 | ~~`validate_config()` runs after constructor~~ | ~~All providers~~ | **FIXED** API key checked at START of `__init__` before SDK client is created; raises `ProviderConfigError` immediately. |
| 28 | ~~Copy-paste providers~~ | ~~`openai_provider.py` ~ `groq_provider.py`~~ | **FIXED** Shared `generate()` extracted to `OpenAICompatibleProvider` in `base.py`; `_classify_error()` hook for typed exceptions. |
| 29 | ~~`print()` used instead of logging~~ | ~~`ollama_provider.py:93,96,248,250`~~ | **FIXED** All `print()` replaced with `logger.info()`. |
| 30 | ~~Bare `except:` clause~~ | ~~`ollama_provider.py:211`~~ | **FIXED** Changed to `except Exception:`. |
| 31 | ~~Provider SDK packages not in `pyproject.toml`~~ | ~~`pyproject.toml`~~ | **FIXED** Added `openai`, `anthropic`, `groq`, `google-generativeai` as optional extras. `pip install glcs[anthropic]` and `glcs[all-providers]` now work. |

### 3.3 Thread Safety & Performance

| # | Issue | File | Details |
|---|-------|------|---------|
| 32 | ~~Thread-unsafe singleton~~ | ~~`glcs/core/semantic_encoder.py:62-64,96-105`~~ | **FIXED** Added `_lock: threading.Lock` at class level. `_load_model()` uses double-checked locking; `clear_model_cache()` also holds the lock. |
| 33 | ~~Docstring lies about lazy loading~~ | ~~`glcs/core/semantic_encoder.py:75-80`~~ | **FIXED** Docstring now correctly says model loads eagerly on construction and is cached for reuse. |
| 34 | ~~Eager imports load entire ML stack~~ | ~~`glcs/core/__init__.py:12-24`~~ | **FIXED** `glcs/core/__init__.py` now uses Python's `__getattr__` lazy-import pattern. ML libraries are only loaded on first attribute access. |
| 35 | ~~`list_contexts` fetches all forms~~ | ~~`memory_manager.py:521-532`~~ | **FIXED** Paginates with `limit=1000`/`offset` so at most 1000 metadata dicts are in memory at once. |
| 36 | ~~`get_context_stats` reconstructs full objects~~ | ~~`memory_manager.py:590`~~ | **FIXED** Now queries `include=["metadatas"]` only — no embeddings or documents loaded. Stats computed directly from stored metadata fields. |

### 3.4 Data Model Issues

| # | Issue | File | Details |
|---|-------|------|---------|
| 37 | ~~Hardcoded 768-dim everywhere~~ | ~~`models.py:218`, `semantic_encoder.py:79,143,210`, `memory_manager.py:367`~~ | **FIXED** Embedding validator now accepts any non-empty 1D array — dimension check removed from model. SemanticEncoder remains the authority on dimension. |
| 38 | ~~`violation_type` is unvalidated string~~ | ~~`models.py:262`~~ | **FIXED** `ViolationType(str, Enum)` added with 4 values (`POLARITY_CONTRADICTION`, `UNIVERSAL_GROUND_CONTRADICTION`, `EXACT_REDUNDANCY`, `SEMANTIC_REDUNDANCY`). `Violation.violation_type` now typed. |
| 39 | ~~`severity` validated by regex, not enum~~ | ~~`models.py:264`~~ | **FIXED** `Severity(str, Enum)` added (`HIGH`, `MEDIUM`, `LOW`). `Violation.severity` now typed. Full IDE autocomplete. |
| 40 | ~~`ConsistencyReport.is_consistent` requires manual sync~~ | ~~`models.py:303-316`~~ | **FIXED** `is_consistent` is now a `@computed_field` — auto-derived from `len(violations) == 0`. Cannot be set manually. `ConsistencyChecker` updated to stop passing it. |
| 41 | ~~Lossy storage round-trip~~ | ~~`memory_manager.py:647-695`~~ | **FIXED** `_build_metadata()` stores full `form_json` (Pydantic JSON, embedding excluded) in ChromaDB metadata. `_reconstruct_form()` deserialises from JSON — all entity IDs, relation IDs, relation_type, and metadata dicts fully preserved. |
| 42 | ~~Metadata duplication~~ | ~~`memory_manager.py:155-163, 254-263`~~ | **FIXED** `_build_metadata(form)` helper extracted. `store_form` and `update_form` both call it — single source of truth. |

### 3.5 Dead Code & Unused Imports

| # | Issue | File | Details |
|---|-------|------|---------|
| 43 | ~~`augmented_prompt` is dead code~~ | ~~`llm_wrapper.py:246-250`~~ | **FIXED** `augmented_prompt` now actually sent to the LLM — history slice replaced with augmented version when context exists. History itself keeps the original prompt for clean multi-turn display. |
| 44 | ~~`validate_config` never returns False~~ | ~~`glcs/utils/config_manager.py:110-180`~~ | **FIXED** Return type changed to `None`. Dead `if not validate_config()` branch removed from `load_config` — replaced with plain call. |
| 45 | ~~`_convert_messages` is dead code~~ | ~~`glcs/providers/base.py:91-103`~~ | **FIXED** Method deleted — no provider ever overrode it and no code ever called it. |
| 46 | ~~Unused imports~~ | ~~Various~~ | **FIXED** Removed: `format_exception_message` + `Path` (memory_manager.py), `uuid4` (logical_parser.py), `Tuple` (consistency_checker.py), `Optional` (all 5 provider files). |

### 3.6 API & Security

| # | Issue | File | Details |
|---|-------|------|---------|
| 47 | ~~Exception details leaked to client~~ | ~~`glcs/api/routes.py:153,165,267,324`~~ | **FIXED** Raw exceptions sanitized to "Internal server error occurred." or similar generic messages. |
| 48 | ~~Global exception handler shadows HTTPException~~ | ~~`glcs/api/app.py:176-191`~~ | **FIXED** Added `isinstance(exc, StarletteHTTPException)` check to re-raise standard FastAPI errors. |
| 49 | ~~Startup failure silently swallowed~~ | ~~`glcs/api/app.py:67-69`~~ | **FIXED** Replaced logger.warning with `raise RuntimeError` to ensure hard failure if GLCS cannot initialize. |
| 50 | ~~`glcs: AdvancedGLCS = None` wrong type~~ | ~~`glcs/api/routes.py:33`~~ | **FIXED** Changed type hint to `Optional[AdvancedGLCS]`. |
| 51 | ~~Pydantic V1 syntax in API models~~ | ~~`glcs/api/models.py`~~ | **FIXED** All models updated to Pydantic V2 (ConfigDict, json_schema_extra). |
| 52 | ~~API key exposed in `ProviderConfig.__repr__`~~ | ~~`glcs/providers/base.py`~~ | **FIXED** Custom `__repr__` added to `ProviderConfig` that masks `api_key`. |

### 3.7 Test Quality

| # | Issue | Details |
|---|-------|---------|
| 53 | ~~Fake test patterns~~ | **FIXED** Removed empty `except: pass` in `test_provider_system.py`. Validated `assert True` and `assert isinstance(x, object)` were already cleaned up or replaced with meaningful assertions in smoke and parser tests. |
| 54 | Integration tests mock the LLM | `test_advanced_glcs.py` — every test mocks `_call_llm`. These are unit tests in disguise, not integration tests. |
| 55 | ~~Stale test assertion~~ | ~~`test_llm_parser.py:59`~~ | **FIXED** Updated assertion: Ollama default model is `qwen2.5:0.5b`. |
| 56 | Register markers | `requires_api_key` marker is used but not registered in `pytest.ini`. Causes warnings. |
| 57 | ~~No `conftest.py`~~ | **FIXED** Created `tests/conftest.py` and moved common fixtures (`memory_manager`, `encoder`, `advanced_glcs`) there. Reduced duplication in 4+ files. |

### 3.8 Project Packaging


| # | Issue | Details |
|---|-------|---------|
| 58 | Missing PyPI metadata | No `license`, `classifiers`, `keywords`, `homepage`, `repository` fields in `pyproject.toml`. |
| 59 | `authors = ["PhD Project"]` | Not in standard `"Name <email>"` format. Will cause issues during PyPI publication. |
| 60 | ~~No CLI entry point~~ | ~~`glcs/cli.py`~~ | **FIXED** Created full-featured CLI using `argparse` with support for processing, verifying, searching, and clearing contexts. Added entry point to `pyproject.toml`. |
| 61 | ~~Log rotation missing~~ | ~~`config/logging.yaml`~~ | **FIXED** Updated `file` and `error_file` handlers to use `RotatingFileHandler` with 10MB limit and 5 backups. Added unit test verification. |
| 62 | `glcs/hierarchical/` is empty | Empty placeholder subpackage with no modules. Remove or document as future work. |
| 63 | ~~Advanced API not exported~~ | ~~`glcs/__init__.py`~~ | **FIXED** `glcs/__init__.py` now exports all key advanced components (`AdvancedGLCS`, `LLMLogicalParser`, `LogicalForm`, etc.) with `__getattr__` lazy loading to prevent eager heavy imports. |
| 64 | ~~Dual config systems~~ | ~~`glcs/config.py`~~ | **FIXED** Unified into a single system in `glcs/config.py`. `glcs/utils/config_manager.py` now serves as a compatibility bridge. Added validation and env overrides. |
| 65 | `.env.template` incomplete | Only documents 3 API keys. Missing: `GROQ_API_KEY`, `OLLAMA_ENDPOINT`, `OLLAMA_MODEL`, `GLCS_DEFAULT_PROVIDER`, `GLCS_TEMPERATURE`, `GLCS_MAX_TOKENS`, and all model override vars. |


### 3.9 Previously Identified Gaps (from original audit)

| # | Issue | File | Details |
|---|-------|------|---------|
| 66 | ~~Missing `embedding_dim` property~~ | ~~`glcs/core/semantic_encoder.py`~~ | **FIXED** `embedding_dim` now exposed as a `@property`. Updated all unit tests to use the property instead of hardcoded 768. |
| 67 | ~~`search_by_entity` missing `context_id` support~~ | ~~`glcs/core/memory_manager.py`~~ | **FIXED** Method already supported `context_id`. Added unit test verification to ensure filtering works correctly across contexts. |
| 68 | ~~Missing `save_state()`/`load_state()` methods~~ | ~~`glcs/advanced_wrapper.py`~~ | **FIXED** Implemented explicit JSON-based state export/import in `MemoryManager` and exposed via `AdvancedGLCS`. Ensures portability across environments. Added unit test. |
| 69 | ~~Missing `clear_all()` method~~ | ~~`glcs/core/memory_manager.py`~~ | **FIXED** `clear_all()` implemented in `MemoryManager` and exposed via `AdvancedGLCS`. Added 2 unit tests and 1 integration test. |
| 70 | ~~`switch_provider` half-updates on failure~~ | ~~`glcs/core/logical_parser.py:537-555`~~ | **FIXED** Implemented atomic switching — internal state (`provider_name`, `_model`, etc.) is only updated AFTER successful `ProviderFactory.create()` call. Added regression test. |
| 71 | ~~`_validate_extraction` mutates input~~ | ~~`glcs/core/logical_parser.py:349-365`~~ | **FIXED** Refactored to a pure function that returns a new validated dictionary with defaults applied. Input dictionary remains untouched. Added unit test. |
| 72 | ~~`parse_batch` silently drops failures~~ | ~~`glcs/core/logical_parser.py:479-485`~~ | **FIXED** Now returns a `BatchResult` object containing both successful `LogicalForm`s and a list of `BatchError`s with full error details. Updated API and unit tests. |
| 73 | ~~`process_batch` silently drops failures~~ | ~~`glcs/advanced_wrapper.py:212-217`~~ | **FIXED** Now returns a `BatchResult` object containing both successful `ConsistencyReport`s and error details for transparent batch processing. Updated demo examples. |
| 74 | ~~`delete_form` silently succeeds when form doesn't exist~~ | ~~`memory_manager.py:292`~~ | **FIXED** Added existence check before deletion. `delete_form()` now returns `True` if deleted, `False` if not found. Updated unit tests. |
| 75 | ~~`update_form` wasteful existence check~~ | ~~`memory_manager.py:243-247`~~ | **FIXED** Replaced expensive `retrieve_form()` with a lightweight `collection.get(include=[])` ID-only check to avoid full object reconstruction. |
| 76 | ~~`_check_redundancy` order-of-operations bug~~ | ~~`consistency_checker.py:470-479`~~ | **FIXED** Redundancy checks now explicitly require the same polarity before text or semantic similarity is checked. Added 2 regression tests. |
| 77 | ~~`_calculate_severity` has dead branches~~ | ~~`consistency_checker.py:565-569`~~ | **FIXED** Removed dead branches for REDUNDANCY and UNIVERSAL_GROUND_CONTRADICTION; these types now have their severity set directly at the violation site. |
| 78 | ~~Gemini model recreated every call~~ | ~~`glcs/providers/gemini_provider.py:99-103`~~ | **FIXED** Implemented caching for `GenerativeModel` instances with system instructions. Re-uses instances when instruction matches. Added unit test. |
| 79 | ~~History unbounded in `llm_wrapper.py`~~ | ~~`glcs/llm_wrapper.py:95,255,280`~~ | **FIXED** Implemented sliding window for conversation history using `GLCS_MAX_HISTORY` (default 50). Added unit test for history enforcement. |
| 80 | ~~`load_dotenv()` at import time~~ | ~~`glcs/llm_wrapper.py:23`~~ | **FIXED** Moved `load_dotenv()` from global scope to `GLCSWrapper.__init__` to prevent test environment contamination. |
| 81 | Logging fallback hides config problems | `glcs/utils/logger.py:126-134` | Missing config file silently falls back to basicConfig. No warning emitted. |
| 82 | ~~No `__repr__` for LogicalForm~~ | ~~`glcs/core/models.py`~~ | **FIXED** Custom `__repr__` implemented for `LogicalForm` that summarizes metadata and hides the massive 768-float embedding array. Added `__str__` for friendly display. |
| 83 | ~~Mutable default in ProviderConfig~~ | ~~`glcs/providers/base.py:18`~~ | **FIXED** Replaced `extra: Dict = None` with `field(default_factory=dict)`. |

---

## Progress Tracker

| Tier | Total | Fixed | Remaining |
|------|-------|-------|-----------|
| Tier 1: Critical | 10 | 10 | 0 |
| Tier 2: Data Integrity | 10 | 10 | 0 |
| Tier 3: Engineering Quality | 63 | 57 | 6 |
| **Total** | **83** | **77** | **6** |

---

**Last Updated:** 2026-04-21 (Tier 3 — #23, #47–#53, #57, #60, #61, #63, #64, #66–#74, #76–#80, #82, #83 fixed)
**Audited By:** Claude Opus 4.6 (full codebase audit)

