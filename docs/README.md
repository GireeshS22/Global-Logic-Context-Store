# GLCS Documentation

Welcome to the hosted documentation for GLCS. Start here if you installed the package with `pip install glcs` and want a stable reference for the Python API, quickstart flow, provider setup, and REST endpoints.

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

- The simple, stable imports are available from the top-level `glcs` package.
- The advanced LLM and REST modules are documented here as public APIs, but they may still evolve between releases.
- Examples in the guides are aligned with the current package version and the current REST API route prefixes.

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
