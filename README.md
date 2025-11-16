# GLCS - Global Logical Context Store

**Version**: 0.1.0 (MVP)
**Status**: Development
**License**: MIT

## Overview

GLCS (Global Logical Context Store) is a neuro-symbolic middleware system designed to enforce logical consistency in Large Language Models. It acts as an external validation layer that intercepts, parses, validates, and stores logical statements to prevent model self-contradiction.

## Key Features

- **Real-time Consistency Checking**: Validates statements against stored logical memory
- **Hierarchical Memory**: Organizes statements by logical type (Universal, Existential, Conditional, Ground)
- **Model-Agnostic**: Works with any LLM API (OpenAI, Anthropic, Google)
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

```python
from glcs import GLCSManager

# Initialize GLCS
glcs = GLCSManager()

# Process a statement
result = glcs.process_statement(
    text="All employees work remotely",
    context_id="conversation-123"
)

# Check consistency
if result.is_consistent:
    print("Statement is consistent!")
else:
    print(f"Violations found: {result.violations}")
```

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
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=glcs

# Run specific test file
poetry run pytest tests/unit/test_models.py
```

### Code Formatting

```bash
# Format code with Black
poetry run black glcs/ tests/

# Lint with Ruff
poetry run ruff check glcs/ tests/
```

## Documentation

- [API Documentation](docs/API.md) - REST API reference
- [Development Guide](docs/DEVELOPMENT.md) - Architecture and implementation details
- [Evaluation Results](docs/EVALUATION.md) - Benchmarks and performance

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
