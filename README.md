# GLCS - Global Logical Context Store

**Version**: 2.1.0 (Stage 2.1 - REST API)
**Status**: Development
**License**: MIT

[![Documentation Status](https://readthedocs.org/projects/glcs/badge/?version=latest)](https://glcs.readthedocs.io/en/latest/)

Hosted documentation: https://glcs.readthedocs.io/

## Overview

GLCS (Global Logical Context Store) is a neuro-symbolic middleware system designed to enforce logical consistency in Large Language Models. It acts as an external validation layer that intercepts, parses, validates, and stores logical statements to prevent model self-contradiction.

## Key Features

### 🎯 Stage 1.5 (Current) - Advanced LLM Parser
- **LLM-Based Parsing**: Understands complex natural language using GPT-4, Claude, Gemini, or local Ollama
- **Configurable Embeddings**: Semantic similarity search using sentence transformers — encoder model and dimension are configurable
- **Vector Memory**: ChromaDB-powered storage with efficient similarity search and lossless round-trip (entity IDs, relation types, and metadata fully preserved)
- **Advanced Consistency Checking**: Detects contradictions using semantic similarity
- **Multi-Provider Support**: Works with 5 LLM providers (Ollama, OpenAI, Anthropic, Gemini, Groq)
- **Offline Mode**: 100% free local operation with Ollama

### 🏗️ Architecture
- **Real-time Consistency Checking**: Validates statements against stored logical memory
- **Hierarchical Memory**: Organizes statements by logical type (Universal, Existential, Conditional, Ground)
- **Model-Agnostic**: Works with any LLM API (OpenAI, Anthropic, Google, Groq, Ollama)
- **Neuro-Symbolic Approach**: Combines vector embeddings with symbolic logical rules

## Installation

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Global-Logic-Context-Store
   ```

2. **Install dependencies using Poetry**
   ```bash
   poetry install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.template .env
   # Edit .env and add your API keys
   ```

4. **Verify installation**
   ```bash
   poetry run pytest tests/
   ```

## Quick Start

### Advanced Mode (Stage 1.5) - Recommended

```python
from glcs.advanced_wrapper import AdvancedGLCS

# Initialize Advanced GLCS with Ollama (free, local)
glcs = AdvancedGLCS(
    parser_provider='ollama',  # Free local LLM
    encoder_model='all-mpnet-base-v2',  # 768-dim embeddings
)

# Process statements
report = glcs.process_statement(
    "All employees must complete training",
    context_id="company-policies"
)

if report.is_consistent:
    print("✓ Statement stored successfully")
else:
    print("⚠️  Inconsistency detected:")
    for violation in report.violations:
        print(f"  - {violation.explanation}")

# Search for similar statements
similar = glcs.search_similar(
    "Who needs training?",
    context_id="company-policies",
    top_k=5
)
```

### Simple Mode (Stage 1.4) - For Simple Use Cases

```python
from glcs import GLCSWrapper

# Initialize with any provider
wrapper = GLCSWrapper(provider='ollama', model='qwen2.5:0.5b')

# Generate with consistency checking
result = wrapper.generate("What is 2 + 2?")
print(result['response'])
```

See `examples/advanced_glcs_demo.py` for complete examples!

## REST API (Stage 2.1) 🚀 NEW!

GLCS now provides a production-ready REST API for remote access:

### Quick API Start

```bash
# 1. Start the API server
poetry run uvicorn glcs.api.app:app --reload

# 2. Open interactive docs
# Browser: http://localhost:8000/docs
```

### API Examples

```bash
# Parse a statement
curl -X POST http://localhost:8000/api/v1/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "John is a manager", "context_id": "team-db"}'

# Check consistency
curl -X POST http://localhost:8000/api/v1/check \
  -H "Content-Type: application/json" \
  -d '{"text": "John is a developer", "context_id": "team-db"}'

# Semantic search
curl "http://localhost:8000/api/v1/search?query=managers&context_id=team-db"
```

### Python Client Example

```python
import requests

# Parse statement via API
response = requests.post('http://localhost:8000/api/v1/parse', json={
    'text': 'All managers must approve budgets',
    'context_id': 'company-policies'
})
result = response.json()
print(f"Parsed as: {result['logical_type']}")
print(f"Confidence: {result['confidence_score']}")
```

**Full API Documentation:** [docs/API_GUIDE.md](docs/API_GUIDE.md)

## Project Structure

```
Global-Logic-Context-Store/
├── glcs/                  # Main package
│   ├── core/             # Core components (parser, encoder, memory, checker)
│   ├── hierarchical/     # Hierarchical logic modules
│   ├── utils/            # Utilities (config, logging, exceptions)
│   └── api/              # REST API layer
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── fixtures/        # Test data
├── examples/            # Example scripts
├── data/                # Datasets and memory storage
├── config/              # Configuration files
├── docs/                # Documentation
├── scripts/             # Utility scripts
└── baselines/           # Baseline implementations

```

## Development

### Running Tests

```bash
# Run all unit tests (234 tests)
poetry run pytest tests/unit/ -q

# Run with coverage
poetry run pytest tests/unit/ --cov=glcs --cov-report=term-missing

# Run a specific file
poetry run pytest tests/unit/test_models.py

# Stop on first failure
poetry run pytest tests/unit/ -x
```

See [tests/README.md](tests/README.md) for the full testing guide — per-file descriptions, example test code, TDD guidelines, and stage status.

### Code Formatting

```bash
# Format code with Black
poetry run black glcs/ tests/

# Lint with Ruff
poetry run ruff check glcs/ tests/
```

## Documentation

### Stage 1.5 (Advanced Implementation)
- [LLM Parser Guide](docs/LLM_PARSER_GUIDE.md) - **NEW**: Complete guide to LLM-based parsing
- [Provider Guide](docs/PROVIDER_GUIDE.md) - Multi-LLM provider comparison
- [Ollama Setup](docs/OLLAMA_SETUP.md) - Free local LLM setup
- [Core Components](glcs/core/README.md) - Architecture deep dive (1386 lines!)
- [Utils Documentation](glcs/utils/README.md) - Configuration, logging, exceptions

### General
- [Testing Guide](tests/README.md) - Full test suite guide (234 tests, per-file descriptions, TDD guidelines)
- [Build Principles](docs/BUILD_PRINCIPLES.md) - Engineering standards all contributors must follow
- [Configuration Guide](config/README.md) - YAML configuration reference

## Research

This project is part of a PhD research on logical consistency in LLMs.

**Research Questions**:
1. Can hierarchical memory improve LLM consistency?
2. What logical structures are sufficient for consistency checking?
3. Can real-time validation prevent self-contradiction?

## License

MIT License - See LICENSE file for details

## Contributing

This is a research project. For questions or collaboration, please contact the project lead.

## Acknowledgments

- Sentence-Transformers for embedding models
- OpenAI for LLM APIs
- Poetry for dependency management
