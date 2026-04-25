# GLCS Documentation

> **A middleware layer that stops LLMs from contradicting themselves.**

GLCS (Global Logical Context Store) sits between your application and any LLM. Every statement the model makes gets parsed into a logical form, stored in a vector memory, and checked for consistency against everything it has said before. If it contradicts itself — GLCS catches it, scores the conflict, and flags it before it reaches the user.

---

## What it does

1. **Parse** — natural language in, structured logical form out (subject, predicate, object, type, polarity)
2. **Store** — every statement is embedded (768-dim vectors via sentence-transformers) and saved to ChromaDB
3. **Check** — new statements are compared against stored ones for contradictions, redundancies, and rule violations
4. **Report** — a `ConsistencyReport` with severity scores and explanations is returned in real time

It works with **7 LLM providers** out of the box: OpenAI, Anthropic, Gemini, Groq, Together AI, xAI (Grok), and Ollama (free local).

---

## Current Status

**Version:** 0.1.0 — core pipeline complete, REST API live, publishing to PyPI in progress.

| Component | Status |
|---|---|
| Data models (LogicalForm, Violation, ConsistencyReport) | Complete |
| Semantic encoder (768-dim embeddings) | Complete |
| Vector memory (ChromaDB) | Complete |
| Consistency checker | Complete |
| LLM logical parser (all 7 providers) | Complete |
| REST API (FastAPI) | Complete |
| PyPI packaging | In progress |

---

## Guides

| Guide | What it covers |
|---|---|
| [Provider Guide](PROVIDER_GUIDE.md) | All 7 providers — setup, pricing, when to use each |
| [LLM Parser Guide](LLM_PARSER_GUIDE.md) | How parsing works, usage examples, API reference |
| [REST API Guide](API_GUIDE.md) | HTTP endpoints, curl examples, Python client |
| [Ollama Setup](OLLAMA_SETUP.md) | Free local LLM — install, models, troubleshooting |
| [Build Principles](BUILD_PRINCIPLES.md) | Engineering standards all contributors must follow |

---

## Quick Start

```bash
pip install glcs[openai]   # or: [anthropic] [gemini] [groq] [all-providers]
cp .env.template .env      # add your API key
```

```python
from glcs.advanced_wrapper import AdvancedGLCS

glcs = AdvancedGLCS(parser_provider='openai')

# First statement — stored fine
report = glcs.process_statement("All employees must complete training", context_id="hr")

# Second statement — contradiction caught
report = glcs.process_statement("Bob does not need training", context_id="hr")

if not report.is_consistent:
    for v in report.violations:
        print(f"{v.severity}: {v.explanation}")
```

Or run the REST API:

```bash
poetry run uvicorn glcs.api.app:app --reload
# Interactive docs at http://localhost:8000/docs
```

---

## Testing providers

Before deploying, verify all configured providers work end-to-end:

```bash
poetry run python scripts/smoke_test_providers.py
```

Shows exact messages sent, responses received, and consistency scores for each provider.

---

## Repository

[https://github.com/GireeshS22/Global-Logic-Context-Store](https://github.com/GireeshS22/Global-Logic-Context-Store)
