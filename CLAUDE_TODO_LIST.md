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
| 22 | Polarity check is trivially narrow | `consistency_checker.py:286-320` | Requires BOTH exact structural match (same subject/predicate/object names) AND high embedding similarity. Can only catch the trivial case of exact same words with "not" added. Any paraphrase contradiction is missed. |
| 23 | O(n^2) pairwise comparisons | `consistency_checker.py:263-268, 447-452` | No indexing, batching, or early exit. 1000 forms = 500K comparisons. Embedding comparisons should be a single matrix multiply. |

### 3.2 Provider System

| # | Issue | Files | Details |
|---|-------|-------|---------|
| 24 | String-based error classification | All 5 providers | `str(e).lower()` substring matching instead of catching SDK typed exceptions (`openai.RateLimitError`, etc.). Fragile, loses error context. |
| 25 | Factory crashes on re-import | `glcs/providers/factory.py:28-29` | `register()` raises `ValueError` on duplicate name. If `glcs.providers` is re-imported or `clear()` is called, the factory breaks. |
| 26 | Ollama auto-pulls models without consent | `glcs/providers/ollama_provider.py:92-103` | Constructor silently downloads multi-GB models. Dangerous in CI/CD. Should be opt-in. |
| 27 | `validate_config()` runs after constructor | All providers | By the time validation runs, the client is already initialized with potentially invalid credentials. Validation is theater. |
| 28 | Copy-paste providers | `openai_provider.py` ~ `groq_provider.py` | Near-identical `generate()` methods. The base class `_convert_messages()` hook exists but is unused. No actual abstraction. |
| 29 | `print()` used instead of logging | `ollama_provider.py:93,96,248,250` | Library code should never use `print()`. Use `logger.info()`. |
| 30 | Bare `except:` clause | `ollama_provider.py:211` | Catches everything including `KeyboardInterrupt` and `SystemExit`. Use `except Exception:`. |
| 31 | Provider SDK packages not in `pyproject.toml` | `pyproject.toml` | `anthropic`, `google-generativeai`, `groq` are not listed as optional extras. Users cannot `pip install glcs[anthropic]`. |

### 3.3 Thread Safety & Performance

| # | Issue | File | Details |
|---|-------|------|---------|
| 32 | Thread-unsafe singleton | `glcs/core/semantic_encoder.py:62-64,96-105` | Docstring claims "thread-safe singleton" but has zero locking. Two threads can both load the 420MB model simultaneously. Add `threading.Lock`. |
| 33 | Docstring lies about lazy loading | `glcs/core/semantic_encoder.py:75-80` | Docstring says "loaded lazily on first encode() call" but `_load_model()` is called in `__init__`. Model loads eagerly on construction. |
| 34 | Eager imports load entire ML stack | `glcs/core/__init__.py:12-24` | Importing `Entity` from `glcs.core` triggers loading of sentence-transformers, ChromaDB, and LLM libraries. Use lazy imports. |
| 35 | `list_contexts` fetches all forms | `memory_manager.py:521-532` | Loads every metadata dict into memory just to extract unique context IDs. Will OOM at scale. |
| 36 | `get_context_stats` reconstructs full objects | `memory_manager.py:590` | Builds full `LogicalForm` objects (including numpy arrays) just to count types. Should query metadata only. |

### 3.4 Data Model Issues

| # | Issue | File | Details |
|---|-------|------|---------|
| 37 | Hardcoded 768-dim everywhere | `models.py:218`, `semantic_encoder.py:79,143,210`, `memory_manager.py:367` | Embedding dimension baked into validators. Cannot swap encoder model without touching code in 3 files. `self.embedding_dim` attribute exists on SemanticEncoder but is unused by the validation checks. |
| 38 | `violation_type` is unvalidated string | `models.py:262` | No enum, any string passes. Compare to `LogicalType` and `Polarity` which are proper enums. |
| 39 | `severity` validated by regex, not enum | `models.py:264` | Uses `pattern="^(HIGH\|MEDIUM\|LOW)$"` instead of a `Severity` enum. No IDE autocomplete, no type safety. |
| 40 | `ConsistencyReport.is_consistent` requires manual sync | `models.py:303-316` | Caller must manually compute `is_consistent = (len(violations) == 0)` and pass it. Should be a computed field. |
| 41 | Lossy storage round-trip | `memory_manager.py:647-695` | `store_form()` -> `retrieve_form()` loses `entity_type`, `relation_type`, `metadata`, all entity UUIDs. Reconstructed entities get new random IDs. |
| 42 | Metadata duplication | `memory_manager.py:155-163, 254-263` | Identical metadata dict construction in `store_form` and `update_form`. DRY violation. |

### 3.5 Dead Code & Unused Imports

| # | Issue | File | Details |
|---|-------|------|---------|
| 43 | `augmented_prompt` is dead code | `llm_wrapper.py:246-250` | Context augmentation is built but never sent to the LLM. The entire memory-augmented generation feature is fake. The `_build_context` method has zero effect on actual LLM calls. |
| 44 | `validate_config` never returns False | `glcs/utils/config_manager.py:110-180` | Return type is `bool` but only ever returns `True` or raises. The `if not validate_config()` check in caller is dead code. |
| 45 | `_convert_messages` is dead code | `glcs/providers/base.py:91-103` | No provider overrides it, no code calls it. |
| 46 | Unused imports | Various | `format_exception_message` (memory_manager.py:33), `Path` (memory_manager.py:24), `uuid4` (logical_parser.py:27), `Tuple` (consistency_checker.py:29), `Optional` (all provider files). |

### 3.6 API & Security

| # | Issue | File | Details |
|---|-------|------|---------|
| 47 | Exception details leaked to client | `glcs/api/routes.py:153,165,267,324` | Raw `str(e)` in HTTP responses. Can expose internal paths, DB errors, stack traces. Sanitize before returning. |
| 48 | Global exception handler shadows HTTPException | `glcs/api/app.py:176-191` | `@app.exception_handler(Exception)` may intercept FastAPI's own 404/422 handlers, turning them into 500s. |
| 49 | Startup failure silently swallowed | `glcs/api/app.py:67-69` | If GLCS init fails, API starts anyway and every endpoint returns 503. Should fail hard or expose a health check. |
| 50 | `glcs: AdvancedGLCS = None` wrong type | `glcs/api/routes.py:33` | Type annotation says `AdvancedGLCS` but value is `None`. Should be `Optional[AdvancedGLCS]`. |
| 51 | Pydantic V1 syntax in API models | `glcs/api/models.py` | Uses `class Config:` (V1) instead of `model_config = ConfigDict(...)` (V2). `min_items` should be `min_length` in V2. |
| 52 | API key exposed in `ProviderConfig.__repr__` | `glcs/providers/base.py` | Default `@dataclass` repr prints `api_key` in plain text in logs/tracebacks. Should mask it. |

### 3.7 Test Quality

| # | Issue | Details |
|---|-------|---------|
| 53 | Fake test patterns | `assert True` (test_smoke.py:49), `assert isinstance(x, object)` (test_parser.py:94), `except Exception: pass` (test_provider_system.py:310). Provide false confidence. |
| 54 | Integration tests mock the LLM | `test_advanced_glcs.py` — every test mocks `_call_llm`. These are unit tests in disguise, not integration tests. |
| 55 | ~~Stale test assertion~~ | ~~`test_llm_parser.py:59`~~ | **FIXED** Updated assertion: Ollama default model is `qwen2.5:0.5b`. |
| 56 | `@pytest.mark.requires_api_key` not registered | `test_provider_system.py` — marker not in `pytest.ini`, tests run unconditionally and fail. |
| 57 | No `conftest.py` | No shared fixtures file. Test setup duplicated across files. |

### 3.8 Project Packaging

| # | Issue | Details |
|---|-------|---------|
| 58 | Missing PyPI metadata | No `license`, `classifiers`, `keywords`, `homepage`, `repository` fields in `pyproject.toml`. |
| 59 | `authors = ["PhD Project"]` | Not in standard `"Name <email>"` format. Will cause issues during PyPI publication. |
| 60 | No CLI entry point | No `[tool.poetry.scripts]` defined. Package has no command-line interface. |
| 61 | No log rotation | `config/logging.yaml` uses append mode with no rotation. Log files grow unbounded. |
| 62 | `glcs/hierarchical/` is empty | Empty placeholder subpackage with no modules. Remove or document as future work. |
| 63 | Advanced API not exported | `glcs/__init__.py:14-15` — `AdvancedGLCS`, `LLMLogicalParser`, etc. are commented out. Users must know internal module paths. |
| 64 | Dual config systems | `glcs/config.py` (ConfigLoader) and `glcs/utils/config_manager.py` (load_config) both provide configuration loading. Unclear which to use. |
| 65 | `.env.template` incomplete | Only documents 3 API keys. Missing: `GROQ_API_KEY`, `OLLAMA_ENDPOINT`, `OLLAMA_MODEL`, `GLCS_DEFAULT_PROVIDER`, `GLCS_TEMPERATURE`, `GLCS_MAX_TOKENS`, and all model override vars. |

### 3.9 Previously Identified Gaps (from original audit)

| # | Issue | File | Details |
|---|-------|------|---------|
| 66 | Missing `embedding_dim` property | `glcs/core/semantic_encoder.py` | `self.embedding_dim = 768` is set but never exposed as a property. Integration tests expect `encoder.embedding_dim` — 5 test failures trace to this. |
| 67 | `search_by_entity` missing `context_id` support | `glcs/core/memory_manager.py` | Integration tests call `search_by_entity(name, context_id=...)` but the method signature or behavior does not properly support the `context_id` filter. |
| 68 | Missing `save_state()`/`load_state()` methods | `glcs/advanced_wrapper.py` | State persistence is implicit via ChromaDB's `persist_directory`. No explicit save/load API. Should be added for clarity and portability. |
| 69 | Missing `clear_all()` method | `glcs/core/memory_manager.py` | `clear_context(context_id)` exists but no global `clear_all()` to wipe the entire store. Needed for testing and reset scenarios. |
| 70 | `switch_provider` half-updates on failure | `glcs/core/logical_parser.py:537-555` | Updates `self.provider_name` before `ProviderFactory.create()`. If factory raises, the object is in an inconsistent state (name changed, provider unchanged). |
| 71 | `_validate_extraction` mutates input | `glcs/core/logical_parser.py:349-365` | A method named "validate" silently mutates the input dict by inserting defaults. Violates single responsibility. |
| 72 | `parse_batch` silently drops failures | `glcs/core/logical_parser.py:479-485` | Failed items logged as warning but dropped. Caller gets a shorter list with no indication which items failed. |
| 73 | `process_batch` silently drops failures | `glcs/advanced_wrapper.py:212-217` | Same pattern — failed statements silently dropped. |
| 74 | `delete_form` silently succeeds when form doesn't exist | `memory_manager.py:292` | ChromaDB's `delete` doesn't error on missing IDs. No way to know if deletion actually happened. |
| 75 | `update_form` wasteful existence check | `memory_manager.py:243-247` | Fully reconstructs a `LogicalForm` (including numpy array) just to verify the form exists, then throws it away. Should use a lightweight ID check. |
| 76 | `_check_redundancy` order-of-operations bug | `consistency_checker.py:470-479` | Exact text match with different polarity is flagged as "EXACT_REDUNDANCY" (LOW severity) instead of contradiction. Polarity check only happens on the semantic redundancy path. |
| 77 | `_calculate_severity` has dead branches | `consistency_checker.py:565-569` | Has branches for "REDUNDANCY" and "UNIVERSAL_GROUND_CONTRADICTION" but those violation types hardcode their severity and never call this method. |
| 78 | Gemini model recreated every call | `glcs/providers/gemini_provider.py:99-103` | Every `generate()` call with a system instruction creates a new `GenerativeModel` instance. Wasteful. |
| 79 | History unbounded in `llm_wrapper.py` | `glcs/llm_wrapper.py:95,255,280` | Conversation history grows without limit. Only sliced for API calls but list itself never trimmed. Memory leak. |
| 80 | `load_dotenv()` at import time | `glcs/llm_wrapper.py:23` | Side effect at import. Contaminates test environments. |
| 81 | Logging fallback hides config problems | `glcs/utils/logger.py:126-134` | Missing config file silently falls back to basicConfig. No warning emitted. |
| 82 | No `__repr__` for LogicalForm | `glcs/core/models.py` | Default Pydantic repr prints the entire 768-float embedding array, making logs unreadable. |
| 83 | Mutable default in ProviderConfig | `glcs/providers/base.py:18` | `extra: Dict[str, Any] = None` patched via `__post_init__`. Should use `field(default_factory=dict)`. |

---

## Progress Tracker

| Tier | Total | Fixed | Remaining |
|------|-------|-------|-----------|
| Tier 1: Critical | 10 | 10 | 0 |
| Tier 2: Data Integrity | 10 | 10 | 0 |
| Tier 3: Engineering Quality | 63 | 2 | 61 |
| **Total** | **83** | **22** | **61** |

---

**Last Updated:** 2026-03-20 (Tier 3 started — #21 fixed)
**Audited By:** Claude Opus 4.6 (full codebase audit)
