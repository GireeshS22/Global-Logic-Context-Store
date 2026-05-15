# GLCS Documentation

Welcome to the hosted documentation for GLCS. Use this home page to reach the quickstart, API reference, provider setup guides, and REST API documentation.

## Start Here

- [Quickstart](quickstart.md) - install, initialize, parse, and check consistency
- [API Reference](api_reference.md) - public Python modules and exports
- [Provider Guide](PROVIDER_GUIDE.md) - provider setup and comparison
- [Ollama Setup](OLLAMA_SETUP.md) - local offline setup
- [REST API Guide](API_GUIDE.md) - HTTP endpoints and examples
- [LLM Parser Guide](LLM_PARSER_GUIDE.md) - advanced parsing workflow

## Project Docs

- [GLCS Documentation](README.md) - full landing page and site map
- [Build Principles](BUILD_PRINCIPLES.md) - repository conventions and engineering standards
- [Cascade Review](CASCADE_REVIEW.md) - dependency impact notes for internal changes
- [Cascade Review Stage 1.5](CASCADE_REVIEW_STAGE1.5.md) - implementation review notes

## Documentation Map

```{toctree}
:maxdepth: 2
:caption: Guides

README
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

## Notes

The site root now resolves to this page as `index.html`, which is required by Read the Docs for serving documentation at the default URL.