# GLCS - Global Logical Context Store

**Version**: 0.1.0  
**Status**: Development  
**License**: MIT

> **A middleware layer that stops LLMs from contradicting themselves.**
>
> GLCS intercepts LLM outputs, extracts logical statements, and checks them for consistency against everything the model has said before — in real time, across any provider.

---

## Overview

GLCS (Global Logical Context Store) is a neuro-symbolic middleware system for enforcing logical consistency in LLM applications. It acts as an external validation layer that parses natural language into logical forms, stores them in a vector memory, and detects contradictions using a combination of semantic similarity and symbolic rule checking.

**Use it when:** your LLM-powered app needs to remember what it has said and catch self-contradictions before they reach the user.

---

## Key Features

- **LLM-Based Parsing**: Understands complex natural language using any supported provider
- **Vector Memory**: ChromaDB-powered storage with semantic similarity search (sentence-transformers)
- **Consistency Checking**: Detects contradictions, redundancies, and logical violations
- **Multi-Provider Support**: 7 LLM providers — OpenAI, Anthropic, Gemini, Groq, Together AI, xAI (Grok), Ollama
- **REST API**: Production-ready HTTP API for remote integration
- **Offline Mode**: 100% free local operation with Ollama

---

## Installation

### Prerequisites

- Python 3.10+
- Poetry (for dependency management)

### Setup

```bash
# 1. Clone
git clone https://github.com/GireeshS22/Global-Logic-Context-Store.git
cd Global-Logic-Context-Store

# 2. Install core dependencies
poetry install

# 3. Install provider SDKs (choose what you need)
poetry install --extras openai       # OpenAI
poetry install --extras anthropic    # Anthropic Claude
poetry install --extras gemini       # Google Gemini
poetry install --extras groq         # Groq
poetry install --extras all-providers  # Everything above

# Together AI and xAI use the openai package — included with --extras openai

# 4. Configure API keys
cp .env.template .env
# Edit .env with your keys
```

---

## Supported Providers

| Provider | Env Key | Default Model | Notes |
|---|---|---|---|
| `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` | |
| `anthropic` / `claude` | `ANTHROPIC_API_KEY` | `claude-haiku-4-5-20251001` | |
| `gemini` / `google` | `GOOGLE_API_KEY` | `gemini-2.5-flash` | Uses `google-genai` SDK |
| `groq` | `GROQ_API_KEY` | `mixtral-8x7b-32768` | Ultra-fast inference |
| `together` | `TOGETHER_API_KEY` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | OpenAI-compatible |
| `xai` / `grok` | `XAI_API_KEY` | `grok-3-mini` | OpenAI-compatible |
| `ollama` | *(none)* | `qwen2.5:0.5b` | Free, local |

---

## Quick Start

### Python API

```python
from glcs.advanced_wrapper import AdvancedGLCS

# Free local mode with Ollama
glcs = AdvancedGLCS(
    parser_provider='ollama',
    encoder_model='all-mpnet-base-v2',
)

report = glcs.process_statement(
    "All employees must complete training",
    context_id="company-policies"
)

if report.is_consistent:
    print("Statement stored successfully")
else:
    for violation in report.violations:
        print(f"Inconsistency: {violation.explanation}")
```

```python
from glcs import GLCSWrapper

# Any cloud provider
wrapper = GLCSWrapper(provider='openai', model='gpt-4o-mini')
result = wrapper.generate("What is 2 + 2?")
print(result['response'])
```

### REST API

```bash
# Start the server
poetry run uvicorn glcs.api.app:app --reload
# Docs at http://localhost:8000/docs

# Parse a statement
curl -X POST http://localhost:8000/api/v1/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "John is a manager", "context_id": "team-db"}'

# Check for contradictions
curl -X POST http://localhost:8000/api/v1/check \
  -H "Content-Type: application/json" \
  -d '{"text": "John is a developer", "context_id": "team-db"}'

# Semantic search
curl "http://localhost:8000/api/v1/search?query=managers&context_id=team-db"
```

---

## Testing Providers (Smoke Test)

Before deploying, verify all configured providers work end-to-end:

```bash
poetry run python scripts/smoke_test_providers.py
```

For each provider with a key in `.env`, this runs three checks and shows the full debug output:

1. **Raw generation** — exact messages sent to the API and response received
2. **Parse test** — LLM extracts a logical form (subject, predicate, type, polarity)
3. **Consistency scoring** — LLM rates two contradictory facts; rule-based checker shows `is_consistent`, `confidence` score, violations, and suggestions

Example output:
```
======================================================================
  PROVIDER: OPENAI  (model: gpt-4o-mini)
======================================================================
  [MESSAGES SENT TO PROVIDER]
  1. role=SYSTEM  You are a concise assistant. Reply in one sentence only.
  2. role=USER    What is the capital of France?
  [RAW PROVIDER RESPONSE]  The capital of France is Paris.
  [OK] Responded in 1.2s
  ...
  SUMMARY
  openai        3/3 tests passed
  anthropic     3/3 tests passed
  gemini        3/3 tests passed
  together      3/3 tests passed
  xai           3/3 tests passed
  All providers passed.
```

---

## Project Structure

```
Global-Logic-Context-Store/
├── glcs/
│   ├── providers/        # LLM provider adapters (OpenAI, Anthropic, Gemini, Groq, Together, xAI, Ollama)
│   ├── core/             # Parser, encoder, memory manager, consistency checker
│   ├── hierarchical/     # Hierarchical logic modules
│   ├── api/              # FastAPI REST layer
│   └── utils/            # Config, logging, exceptions
├── scripts/
│   └── smoke_test_providers.py  # Multi-provider end-to-end test
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── examples/
├── config/               # YAML configuration
├── docs/                 # Guides
└── .env.template         # API key reference
```

---

## Running Tests

```bash
# All unit tests
poetry run pytest tests/unit/ -q

# With coverage
poetry run pytest tests/unit/ --cov=glcs --cov-report=term-missing

# Stop on first failure
poetry run pytest tests/unit/ -x
```

See [tests/README.md](tests/README.md) for the full testing guide.

---

## Configuration

Copy `.env.template` to `.env` and fill in your keys. Key variables:

```bash
GLCS_DEFAULT_PROVIDER=ollama   # Provider used when none specified
GLCS_LOG_LEVEL=INFO
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...
TOGETHER_API_KEY=...
XAI_API_KEY=...
```

Full config reference: [config/README.md](config/README.md)

---

## Documentation

- [Provider Guide](docs/PROVIDER_GUIDE.md) — per-provider comparison and setup
- [LLM Parser Guide](docs/LLM_PARSER_GUIDE.md) — how parsing works
- [Ollama Setup](docs/OLLAMA_SETUP.md) — free local LLM setup
- [API Guide](docs/API_GUIDE.md) — REST API reference
- [Build Principles](docs/BUILD_PRINCIPLES.md) — engineering standards

---

## Research

This project is part of PhD research on logical consistency in LLMs.

**Research Questions:**
1. Can hierarchical memory improve LLM consistency?
2. What logical structures are sufficient for consistency checking?
3. Can real-time validation prevent self-contradiction?

---

## License

MIT License — see LICENSE file for details.

## Contributing

This is a research project. For questions or collaboration, contact the project lead.

## Acknowledgments

- [Sentence-Transformers](https://www.sbert.net/) for embedding models
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [FastAPI](https://fastapi.tiangolo.com/) for the REST layer
- OpenAI, Anthropic, Google, Groq, Together AI, xAI for LLM APIs
- Poetry for dependency management
