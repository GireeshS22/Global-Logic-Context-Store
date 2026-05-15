"""
Multi-provider smoke test for GLCS.

Tests each configured LLM provider end-to-end:
  1. Raw generation -- shows exact messages sent and response received
  2. GLCS parse    -- parses a natural language statement through the LLM
  3. Consistency   -- stores two contradictory facts and scores the conflict

Run:
    poetry run python scripts/smoke_test_providers.py

Keys are read from .env (copy .env.template -> .env and fill in your keys).
Only providers with a key present in the environment are tested.
"""

import os
import sys
import time
import textwrap
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Resolve project root and load .env
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from glcs.providers.base import ProviderConfig, ProviderError  # noqa: E402
from glcs.parser import SimpleParser  # noqa: E402
from glcs.memory import SimpleMemory  # noqa: E402
from glcs.checker import SimpleConsistencyChecker  # noqa: E402

# ---------------------------------------------------------------------------
# Provider registry: (env_key, provider_name, default_model, provider_class)
# ---------------------------------------------------------------------------
def _build_provider_registry():
    entries = []

    try:
        from glcs.providers.openai_provider import OpenAIProvider
        entries.append(("OPENAI_API_KEY", "openai", "gpt-4o-mini", OpenAIProvider))
    except ImportError:
        pass

    try:
        from glcs.providers.anthropic_provider import AnthropicProvider
        entries.append(("ANTHROPIC_API_KEY", "anthropic", "claude-haiku-4-5-20251001", AnthropicProvider))
    except ImportError:
        pass

    try:
        from glcs.providers.gemini_provider import GeminiProvider
        entries.append(("GOOGLE_API_KEY", "gemini", "gemini-2.5-flash", GeminiProvider))
    except ImportError:
        pass

    try:
        from glcs.providers.together_provider import TogetherProvider
        entries.append(("TOGETHER_API_KEY", "together", "meta-llama/Llama-3.3-70B-Instruct-Turbo", TogetherProvider))
    except ImportError:
        pass

    try:
        from glcs.providers.xai_provider import XAIProvider
        entries.append(("XAI_API_KEY", "xai", "grok-3-mini", XAIProvider))
    except ImportError:
        pass

    return entries


# ---------------------------------------------------------------------------
# Pretty-printing helpers
# ---------------------------------------------------------------------------
SEP = "-" * 70

def header(text: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}")

def section(text: str) -> None:
    print(f"\n{SEP}")
    print(f"  {text}")
    print(SEP)

def show_messages(messages: list) -> None:
    print("\n  [MESSAGES SENT TO PROVIDER]")
    for i, msg in enumerate(messages, 1):
        role = msg["role"].upper()
        content = textwrap.fill(msg["content"], width=66, initial_indent="    ", subsequent_indent="    ")
        print(f"  {i}. role={role}")
        print(content)

def show_response(response: str) -> None:
    print("\n  [RAW PROVIDER RESPONSE]")
    wrapped = textwrap.fill(response.strip(), width=66, initial_indent="    ", subsequent_indent="    ")
    print(wrapped)

def ok(msg: str) -> None:
    print(f"  [OK] {msg}")

def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


# ---------------------------------------------------------------------------
# Test 1 -- Raw generation
# ---------------------------------------------------------------------------
RAW_MESSAGES = [
    {"role": "system", "content": "You are a concise assistant. Reply in one sentence only."},
    {"role": "user",   "content": "What is the capital of France?"},
]

def test_raw_generation(provider, provider_name: str) -> bool:
    section(f"TEST 1 -- Raw generation  [{provider_name}]")
    show_messages(RAW_MESSAGES)

    try:
        t0 = time.perf_counter()
        response = provider.generate(RAW_MESSAGES, max_tokens=60)
        elapsed = time.perf_counter() - t0
        show_response(response)
        ok(f"Responded in {elapsed:.2f}s")
        return True
    except ProviderError as e:
        fail(f"ProviderError: {e}")
        return False
    except Exception as e:
        fail(f"Unexpected error: {type(e).__name__}: {e}")
        return False


# ---------------------------------------------------------------------------
# Test 2 -- LLM-assisted parse via GLCS SimpleParser
# The SimpleParser is rule-based (no LLM call needed), but we exercise
# the provider with a structured extraction prompt to show the full cycle.
# ---------------------------------------------------------------------------
PARSE_STATEMENT = "All birds can fly"

PARSE_MESSAGES = [
    {
        "role": "system",
        "content": (
            "You are a logical statement extractor. "
            "Given a natural language statement, respond ONLY with a JSON object "
            "using these exact keys: "
            '{"subject": "<subject>", "predicate": "<predicate>", '
            '"object": "<object_or_null>", "type": "universal|conditional|ground", '
            '"polarity": "positive|negative"}. '
            "No extra text."
        ),
    },
    {
        "role": "user",
        "content": f'Extract the logical form of: "{PARSE_STATEMENT}"',
    },
]

def test_parse(provider, provider_name: str) -> bool:
    section(f"TEST 2 -- GLCS parse  [{provider_name}]")
    print(f"\n  Input statement: \"{PARSE_STATEMENT}\"")
    show_messages(PARSE_MESSAGES)

    try:
        t0 = time.perf_counter()
        response = provider.generate(PARSE_MESSAGES, max_tokens=120, temperature=0.0)
        elapsed = time.perf_counter() - t0
        show_response(response)
        ok(f"Parsed in {elapsed:.2f}s")

        # Also run through the rule-based parser for comparison
        parser = SimpleParser()
        stmt = parser.parse(PARSE_STATEMENT)
        if stmt:
            print(f"\n  [RULE-BASED PARSER RESULT]")
            print(f"    subject   = {stmt.subject}")
            print(f"    predicate = {stmt.predicate}")
            print(f"    object    = {stmt.object}")
            print(f"    type      = {stmt.type.value}")
            print(f"    polarity  = {getattr(stmt, 'polarity', 'n/a')}")
            print(f"    confidence= {stmt.confidence}")
        else:
            print("  [RULE-BASED PARSER] No match (LLM output is authoritative above)")

        return True
    except ProviderError as e:
        fail(f"ProviderError: {e}")
        return False
    except Exception as e:
        fail(f"Unexpected error: {type(e).__name__}: {e}")
        return False


# ---------------------------------------------------------------------------
# Test 3 -- Consistency scoring
# Store two contradictory facts, check the score breakdown.
# ---------------------------------------------------------------------------
FACT_A = "All birds can fly"
FACT_B = "Penguins cannot fly"   # Contradicts the universal rule

CONSISTENCY_MESSAGES_TEMPLATE = [
    {
        "role": "system",
        "content": (
            "You are a logical consistency judge. "
            "Given two statements, rate their consistency on a scale from 0.0 (fully contradictory) "
            "to 1.0 (fully consistent). "
            "Respond ONLY with a JSON object: "
            '{"score": <float>, "verdict": "consistent|contradictory|uncertain", "reason": "<one sentence>"}'
        ),
    },
    {
        "role": "user",
        "content": (
            f'Statement A: "{FACT_A}"\n'
            f'Statement B: "{FACT_B}"\n'
            "Are these consistent?"
        ),
    },
]

def test_consistency(provider, provider_name: str) -> bool:
    section(f"TEST 3 -- Consistency scoring  [{provider_name}]")
    print(f"\n  Fact A: \"{FACT_A}\"")
    print(f"  Fact B: \"{FACT_B}\"")
    show_messages(CONSISTENCY_MESSAGES_TEMPLATE)

    # --- LLM-based scoring ---
    try:
        t0 = time.perf_counter()
        response = provider.generate(CONSISTENCY_MESSAGES_TEMPLATE, max_tokens=150, temperature=0.0)
        elapsed = time.perf_counter() - t0
        show_response(response)
        ok(f"LLM scored in {elapsed:.2f}s")
    except ProviderError as e:
        fail(f"ProviderError during LLM consistency check: {e}")
        return False
    except Exception as e:
        fail(f"Unexpected error: {type(e).__name__}: {e}")
        return False

    # --- Rule-based scoring via SimpleConsistencyChecker ---
    print(f"\n  [RULE-BASED CONSISTENCY CHECK]")
    try:
        parser = SimpleParser()
        memory = SimpleMemory()
        checker = SimpleConsistencyChecker(memory)

        stmt_a = parser.parse(FACT_A)
        if stmt_a:
            memory.store(stmt_a)
            print(f"    Stored A -> subject={stmt_a.subject}, predicate={stmt_a.predicate}, type={stmt_a.type.value}")
        else:
            print(f"    Stored A -> (rule-based parser found no match, skipping rule check)")

        stmt_b = parser.parse(FACT_B)
        if stmt_b:
            print(f"    Checking B -> subject={stmt_b.subject}, predicate={stmt_b.predicate}, type={stmt_b.type.value}")
            is_consistent, score, violations = checker.check_consistency(stmt_b)

            print(f"\n    +- CONSISTENCY RESULT -------------------------")
            print(f"    |  is_consistent : {is_consistent}")
            print(f"    |  confidence    : {score:.3f}  (1.0 = no conflict, 0.0 = contradicted)")
            if violations:
                print(f"    |  violations    :")
                for v in violations:
                    print(f"    |    * {v}")
            else:
                print(f"    |  violations    : none")

            supporting = checker.get_supporting_facts(stmt_b)
            if supporting:
                print(f"    |  supporting    :")
                for s in supporting:
                    print(f"    |    -> \"{s.raw_text}\"")

            suggestion = checker.suggest_alternative(stmt_b, violations)
            if suggestion:
                print(f"    |  suggestion    : {suggestion}")
            print(f"    +-----------------------------------------------")
        else:
            print(f"    B -> (rule-based parser found no match)")

    except Exception as e:
        fail(f"Rule-based checker error: {type(e).__name__}: {e}")

    return True


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_all() -> None:
    header("GLCS Multi-Provider Smoke Test")

    registry = _build_provider_registry()
    configured = []

    for env_key, provider_name, default_model, provider_class in registry:
        api_key = os.getenv(env_key)
        if not api_key:
            print(f"  SKIP  {provider_name:12s}  ({env_key} not set)")
            continue

        model = os.getenv(f"{provider_name.upper()}_MODEL", default_model)
        configured.append((provider_name, api_key, model, provider_class))

    if not configured:
        print("\n  No providers configured. Copy .env.template to .env and add your API keys.")
        sys.exit(1)

    print(f"\n  Providers to test: {', '.join(p[0] for p in configured)}")

    results: dict[str, dict] = {}

    for provider_name, api_key, model, provider_class in configured:
        header(f"PROVIDER: {provider_name.upper()}  (model: {model})")

        try:
            config = ProviderConfig(api_key=api_key, model=model, max_tokens=300, timeout=60)
            provider = provider_class(config)
            print(f"  Initialized: {provider.get_model_info()}")
        except Exception as e:
            fail(f"Failed to initialize {provider_name}: {e}")
            results[provider_name] = {"init": False}
            continue

        r1 = test_raw_generation(provider, provider_name)
        r2 = test_parse(provider, provider_name)
        r3 = test_consistency(provider, provider_name)
        results[provider_name] = {"raw": r1, "parse": r2, "consistency": r3}

    # --- Summary ---
    header("SUMMARY")
    all_passed = True
    for name, res in results.items():
        if not res.get("init", True):
            status = "INIT FAILED"
            all_passed = False
        else:
            passed = sum(1 for v in res.values() if v)
            total = len(res)
            status = f"{passed}/{total} tests passed"
            if passed < total:
                all_passed = False
        print(f"  {name:12s}  {status}")

    print()
    if all_passed:
        print("  All providers passed.")
        sys.exit(0)
    else:
        print("  Some providers failed -- see output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    run_all()
