# GLCS Documentation

Welcome to the hosted documentation for GLCS. This page gives you the big picture, and the sidebar guides take you into setup, API usage, provider selection, and implementation details.

> **A middleware layer that stops LLMs from contradicting themselves.**

GLCS (Global Logical Context Store) sits between your application and any LLM. Every statement the model makes gets parsed into a logical form, stored in vector memory, and checked for consistency against everything it has said before. If it contradicts itself, GLCS catches it before it reaches the user.

---

## What it does

1. **Parse** - natural language in, structured logical form out
2. **Store** - every statement is embedded and saved to ChromaDB
3. **Check** - new statements are compared against stored ones for contradictions and redundancies
4. **Report** - a `ConsistencyReport` is returned with confidence, severity, and explanations

It works with **7 LLM providers** out of the box: OpenAI, Anthropic, Gemini, Groq, Together AI, xAI (Grok), and Ollama.

---

## Start Here

- [Quickstart](quickstart.md) - install, initialize, parse, and check consistency
- [API Reference](api_reference.md) - public Python modules and exports
- [Provider Guide](PROVIDER_GUIDE.md) - provider setup and comparison
- [Ollama Setup](OLLAMA_SETUP.md) - local offline setup
- [REST API Guide](API_GUIDE.md) - HTTP endpoints and examples
- [LLM Parser Guide](LLM_PARSER_GUIDE.md) - advanced parsing workflow

## Project Docs

- [Build Principles](BUILD_PRINCIPLES.md) - repository conventions and engineering standards
- [Cascade Review](CASCADE_REVIEW.md) - dependency impact notes for internal changes
- [Cascade Review Stage 1.5](CASCADE_REVIEW_STAGE1.5.md) - implementation review notes

## Read This First

This site documents the current public API surface of GLCS.

- Stable imports are available from the top-level `glcs` package.
- Advanced LLM and REST modules are public, but may still evolve between releases.
- Examples in these guides are aligned with the current package version and route prefixes.

## Documentation Map

```{toctree}
:maxdepth: 2
:caption: Guides

quickstart
api_reference
PROVIDER_GUIDE
OLLAMA_SETUP
API_GUIDE
LLM_PARSER_GUIDE
BUILD_PRINCIPLES
CASCADE_REVIEW
CASCADE_REVIEW_STAGE1.5
```

## Navigation

Use the Sphinx sidebar to browse the guides and API reference. The same content is available at the hosted docs URL once the Read the Docs project is connected.
