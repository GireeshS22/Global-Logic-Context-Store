# GLCS REST API Guide

**Version:** 2.1.0
**Stage:** 2.1 - REST API
**Last Updated:** 2025-11-18

---

## Quick Start

```bash
# 1. Install dependencies
poetry install

# 2. Make sure Ollama is running
ollama serve

# 3. Pull the model
ollama pull qwen2.5:0.5b

# 4. Start the API server
poetry run uvicorn glcs.api.app:app --reload

# 5. Open http://localhost:8000/docs in your browser
```

**That's it!** Interactive API docs are now at `/docs`.

---

## API Endpoints

### Parse Statement
```bash
curl -X POST http://localhost:8000/api/v1/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "John is a manager", "context_id": "team-db"}'
```

### Check Consistency
```bash
curl -X POST http://localhost:8000/api/v1/check \
  -H "Content-Type: application/json" \
  -d '{"text": "John is a developer", "context_id": "team-db"}'
```

### Search Knowledge
```bash
curl "http://localhost:8000/api/v1/search?query=managers&context_id=team-db"
```

### List Contexts
```bash
curl http://localhost:8000/api/v1/contexts
```

---

## Python Example

```python
import requests

# Parse
response = requests.post('http://localhost:8000/api/v1/parse', json={
    'text': 'John is a manager',
    'context_id': 'team-db'
})
print(response.json())

# Search
response = requests.get('http://localhost:8000/api/v1/search', params={
    'query': 'managers',
    'context_id': 'team-db'
})
print(response.json())
```

---

## Configuration

Set via environment variables:

```bash
export GLCS_PARSER_PROVIDER=ollama        # Default: ollama
export GLCS_PARSER_MODEL=qwen2.5:0.5b     # Default: qwen2.5:0.5b
export GLCS_IN_MEMORY=true                # Default: true
```

---

## Testing

```bash
# Run API tests
poetry run pytest tests/api/ -v

# Test with interactive docs
# 1. Start API: poetry run uvicorn glcs.api.app:app --reload
# 2. Open: http://localhost:8000/docs
# 3. Try endpoints in browser!
```

---

## Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Spec:** http://localhost:8000/openapi.json

---

## Complete Guide

For the hosted documentation, start with [Quickstart](quickstart.md) and [API Reference](api_reference.md), then return here for endpoint-specific request and response examples.
