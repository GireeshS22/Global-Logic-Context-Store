# LLM-Based Logical Parser Guide

**Stage 1.5: Advanced Natural Language Understanding for GLCS**

---

## Table of Contents

1. [Overview](#overview)
2. [Why LLM Parser?](#why-llm-parser)
3. [How It Works](#how-it-works)
4. [Quick Start](#quick-start)
5. [Usage Examples](#usage-examples)
6. [Provider Comparison](#provider-comparison)
7. [Advanced Features](#advanced-features)
8. [Performance Optimization](#performance-optimization)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

---

## Overview

The **LLM-Based Logical Parser** is the research-grade parsing component for GLCS. Unlike regex-based parsers that rely on pattern matching, this parser uses Large Language Models to understand complex natural language and extract structured logical representations.

### Key Features

✅ **Multi-Provider Support**: Works with Ollama (local), OpenAI, Anthropic, Gemini, Groq
✅ **Complex Sentence Handling**: Understands modifiers, clauses, implicit meanings
✅ **Rich Extraction**: Entities, relations, logical types, polarity, confidence
✅ **Intelligent Caching**: Reduces API costs and improves speed
✅ **Retry Logic**: Handles temporary failures with exponential backoff
✅ **Batch Processing**: Process multiple statements efficiently

---

## Why LLM Parser?

### Regex Parser (Stage 1.4) Limitations

The regex-based parser works well for simple, well-structured statements but fails on:

```python
❌ "John, who joined last month, is our new senior manager"
❌ "The system automatically restarts when it detects a crash"
❌ "Despite the challenges, Alice successfully completed the project"
❌ "Employees working remotely must log in by 9 AM"
```

### LLM Parser (Stage 1.5) Advantages

```python
✅ Handles complex sentence structures
✅ Understands implicit relationships
✅ Extracts contextual meanings
✅ Normalizes variations ("manager" = "senior manager" concept)
✅ Detects nuanced logical types
```

### Comparison Example

**Input**: `"John, who recently joined from Google, is our new technical lead"`

| Feature | Regex Parser | LLM Parser |
|---------|-------------|------------|
| **Can Parse?** | ❌ Pattern mismatch | ✅ Yes |
| **Subject Extraction** | ❌ Fails | ✅ "john" |
| **Predicate** | ❌ Fails | ✅ "is" |
| **Object** | ❌ Fails | ✅ "technical lead" |
| **Entity Types** | ❌ No | ✅ person, role |
| **Confidence** | N/A | ✅ 0.92 |

---

## How It Works

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. Input: "All employees must complete training"                 │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│ 2. LLM Parser                                                   │
│    - Sends to LLM with structured prompt                       │
│    - Requests JSON output with specific fields                 │
│    - Temperature: 0.1 (consistent results)                     │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│ 3. LLM Extracts Structure                                       │
│    {                                                            │
│      "subject": {"name": "employees", "type": "person"},       │
│      "predicate": {"verb": "must_complete", "type": "req"},    │
│      "object": {"name": "training", "type": "activity"},       │
│      "logical_type": "universal_rule",                         │
│      "polarity": "positive",                                   │
│      "confidence": 0.92                                        │
│    }                                                            │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│ 4. Validation                                                   │
│    - Check required fields present                             │
│    - Validate field types (logical_type is valid enum)         │
│    - Verify confidence range (0.0-1.0)                         │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│ 5. Create LogicalForm                                           │
│    - Build Entity objects (subject, object)                    │
│    - Build Relation object (predicate)                         │
│    - Set metadata (timestamp, form_id)                         │
│    - Normalize names to lowercase                              │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│ 6. Cache Result                                                 │
│    - Store in memory cache (MD5 hash key)                      │
│    - Reuse for identical inputs                                │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│ 7. Return LogicalForm                                           │
│    - Ready for semantic encoding                               │
│    - Ready for storage in MemoryManager                        │
│    - Ready for consistency checking                            │
└────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Installation

The LLM parser is included in GLCS. No additional installation needed if you have GLCS set up.

### Basic Usage (Ollama - Local & Free)

```python
from glcs.core import LLMLogicalParser

# Initialize with Ollama (default)
parser = LLMLogicalParser()

# Parse a statement
form = parser.parse(
    text="All employees must complete training",
    context_id="company-rules"
)

# Access extracted information
print(f"Subject: {form.subject.name}")        # employees
print(f"Predicate: {form.predicate.verb}")    # must_complete
print(f"Object: {form.object.name}")          # training
print(f"Type: {form.logical_type}")           # LogicalType.UNIVERSAL_RULE
print(f"Polarity: {form.polarity}")           # Polarity.POSITIVE
print(f"Confidence: {form.confidence_score}") # 0.92
```

### Using with OpenAI (Cloud)

```python
from glcs.core import LLMLogicalParser

# Initialize with OpenAI
parser = LLMLogicalParser(
    provider='openai',
    model='gpt-4o-mini',
    api_key='your-api-key'
)

form = parser.parse("John is a manager", "ctx-123")
```

---

## Usage Examples

### Example 1: Simple Ground Fact

```python
parser = LLMLogicalParser()

form = parser.parse("Alice is an engineer", "team-db")

# Result:
# subject: Entity(name='alice', entity_type='person')
# predicate: Relation(verb='is', relation_type='property')
# object: Entity(name='engineer', entity_type='role')
# logical_type: GROUND_FACT
# polarity: POSITIVE
# confidence: 0.96
```

### Example 2: Universal Rule

```python
form = parser.parse("All managers must approve budgets", "policies")

# Result:
# subject: Entity(name='managers', entity_type='person')
# predicate: Relation(verb='must_approve', relation_type='requirement')
# object: Entity(name='budgets', entity_type='object')
# logical_type: UNIVERSAL_RULE
# polarity: POSITIVE
# confidence: 0.94
```

### Example 3: Conditional Logic

```python
form = parser.parse("If the server crashes, it will restart automatically", "system-rules")

# Result:
# subject: Entity(name='server', entity_type='system')
# predicate: Relation(verb='crashes_then_restarts', relation_type='causation')
# object: Entity(name='restart', entity_type='action')
# logical_type: CONDITIONAL_LOGIC
# polarity: POSITIVE
# confidence: 0.89
```

### Example 4: Negative Statement

```python
form = parser.parse("Bob is not a manager", "org-chart")

# Result:
# subject: Entity(name='bob', entity_type='person')
# predicate: Relation(verb='is', relation_type='property')
# object: Entity(name='manager', entity_type='role')
# logical_type: GROUND_FACT
# polarity: NEGATIVE  # ← Note the negative polarity
# confidence: 0.97
```

### Example 5: Complex Sentence

```python
# This would FAIL with regex parser but works with LLM parser
form = parser.parse(
    "John, who recently joined from Google, is our new technical lead",
    "team-db"
)

# Result:
# subject: Entity(name='john', entity_type='person')
# predicate: Relation(verb='is', relation_type='property')
# object: Entity(name='technical lead', entity_type='role')
# logical_type: GROUND_FACT
# polarity: POSITIVE
# confidence: 0.91
```

### Example 6: Batch Processing

```python
parser = LLMLogicalParser()

statements = [
    "Alice is a developer",
    "Bob is a designer",
    "All developers must code review",
    "If system fails, alert admin"
]

forms = parser.parse_batch(statements, context_id="team-kb")

print(f"Parsed {len(forms)}/{ len(statements)} statements")
for form in forms:
    print(f"- {form.logical_type.value}: {form.source_text}")
```

---

## Provider Comparison

### For Parsing Tasks

| Provider | Model | Speed | Accuracy | Cost | Recommended For |
|----------|-------|-------|----------|------|-----------------|
| **Ollama** | llama3.2 | 🟢 Fast | 🟡 Good | 🟢 FREE | Development, testing, offline use |
| **OpenAI** | gpt-4o-mini | 🟢 Fast | 🟢 Excellent | 🟡 Low | Production, high accuracy needed |
| **Anthropic** | claude-3-haiku | 🟢 Fast | 🟢 Excellent | 🟡 Medium | Production, nuanced understanding |
| **Gemini** | gemini-1.5-flash | 🟢 Very Fast | 🟢 Good | 🟢 Very Low | High volume parsing |
| **Groq** | llama-3.1-70b | 🟢 Fastest | 🟡 Good | 🟡 Low | Speed-critical applications |

### Cost Estimates (per 1000 parses)

| Provider | Model | Estimated Cost |
|----------|-------|----------------|
| Ollama | llama3.2 | **$0.00** (local) |
| OpenAI | gpt-4o-mini | ~$0.15 |
| Anthropic | claude-3-haiku | ~$0.25 |
| Gemini | gemini-1.5-flash | ~$0.05 |
| Groq | llama-3.1-70b | ~$0.10 |

---

## Advanced Features

### Feature 1: Caching

The parser automatically caches results to avoid redundant API calls.

```python
parser = LLMLogicalParser(cache_enabled=True)

# First call - hits LLM
form1 = parser.parse("John is a manager", "ctx-1")

# Second call with same text - uses cache (instant, free)
form2 = parser.parse("John is a manager", "ctx-2")

# Check cache stats
stats = parser.get_cache_stats()
print(f"Cache size: {stats['size']}")  # 1

# Clear cache if needed
parser.clear_cache()
```

### Feature 2: Provider Switching

Switch providers dynamically for different use cases.

```python
parser = LLMLogicalParser(provider='ollama')

# Parse with Ollama (free, local)
form1 = parser.parse("Simple statement", "ctx-1")

# Switch to GPT-4 for complex statement
parser.switch_provider('openai', model='gpt-4o')
form2 = parser.parse("Complex sentence with ambiguity", "ctx-1")
```

### Feature 3: Retry Logic

Automatic retry with exponential backoff on failures.

```python
parser = LLMLogicalParser(max_retries=5)

# If LLM call fails temporarily, it will retry:
# - Attempt 1: fail → wait 2s
# - Attempt 2: fail → wait 4s
# - Attempt 3: success ✓
```

### Feature 4: Custom Confidence Threshold

```python
parser = LLMLogicalParser()

form = parser.parse("Ambiguous statement", "ctx-1")

if form.confidence_score < 0.7:
    print("⚠️ Low confidence parse - verify manually")
    # Could fall back to regex parser or ask for clarification
```

---

## Performance Optimization

### Tip 1: Enable Caching

```python
# ✅ Good: Cache enabled (default)
parser = LLMLogicalParser(cache_enabled=True)

# ❌ Bad: Cache disabled (slower, more expensive)
parser = LLMLogicalParser(cache_enabled=False)
```

### Tip 2: Use Batch Processing

```python
# ✅ Good: Batch processing
statements = ["Statement 1", "Statement 2", "Statement 3"]
forms = parser.parse_batch(statements, "ctx-1")

# ❌ Less efficient: One at a time
for stmt in statements:
    form = parser.parse(stmt, "ctx-1")
```

### Tip 3: Choose Right Provider

```python
# For development/testing: Use Ollama (free, offline)
parser = LLMLogicalParser(provider='ollama')

# For production (high accuracy): Use GPT-4o-mini
parser = LLMLogicalParser(provider='openai', model='gpt-4o-mini')

# For high volume (low cost): Use Gemini Flash
parser = LLMLogicalParser(provider='gemini', model='gemini-1.5-flash')
```

### Tip 4: Set Appropriate Timeouts

```python
# Default: 30 seconds
parser = LLMLogicalParser(timeout=30)

# For complex sentences: Increase timeout
parser = LLMLogicalParser(timeout=60)

# For simple statements: Decrease timeout
parser = LLMLogicalParser(timeout=15)
```

---

## Troubleshooting

### Issue 1: Parsing Fails

**Symptoms**: `ParsingError` raised

**Solutions**:
```python
# 1. Check provider is configured
parser = LLMLogicalParser(provider='ollama')
# Make sure Ollama is running: ollama serve

# 2. Increase retries
parser = LLMLogicalParser(max_retries=5)

# 3. Switch to more reliable provider
parser = LLMLogicalParser(provider='openai', api_key='your-key')
```

### Issue 2: Low Confidence Scores

**Symptoms**: `form.confidence_score < 0.5`

**Solutions**:
```python
# 1. Try more powerful model
parser = LLMLogicalParser(provider='openai', model='gpt-4o')

# 2. Simplify input statement
# Instead of: "Despite challenges, the complex system worked"
# Try: "The system worked"

# 3. Check if statement is actually logical
# "How are you?" → Not a logical statement, low confidence expected
```

### Issue 3: Incorrect Logical Type

**Symptoms**: Statement classified as wrong type

**Solutions**:
```python
# 1. Use more explicit language
# Unclear: "Employees sometimes work remotely"
# Clear: "Some employees work remotely" (EXISTENTIAL_CLAIM)

# 2. Switch to higher accuracy model
parser.switch_provider('anthropic', model='claude-3-5-sonnet-20241022')
```

### Issue 4: Slow Performance

**Symptoms**: Parsing takes too long

**Solutions**:
```python
# 1. Enable caching
parser = LLMLogicalParser(cache_enabled=True)

# 2. Use faster provider
parser = LLMLogicalParser(provider='groq')  # Fastest

# 3. Reduce timeout
parser = LLMLogicalParser(timeout=10)

# 4. Use local model (no network latency)
parser = LLMLogicalParser(provider='ollama')
```

---

## API Reference

### `LLMLogicalParser`

```python
class LLMLogicalParser:
    """LLM-powered logical statement parser."""

    def __init__(
        self,
        provider: Optional[str] = 'ollama',
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[Dict] = None,
        cache_enabled: bool = True,
        max_retries: int = 3,
        timeout: int = 30,
    ) -> None:
        """Initialize parser with configuration."""
```

#### Methods

**`parse(text: str, context_id: str, use_cache: bool = True) -> LogicalForm`**

Parse a single natural language statement.

- **Parameters**:
  - `text`: Input statement
  - `context_id`: Context identifier
  - `use_cache`: Whether to use cached result

- **Returns**: `LogicalForm` object with extracted structure

- **Raises**: `ParsingError`, `ValidationError`

---

**`parse_batch(texts: List[str], context_id: str, use_cache: bool = True) -> List[LogicalForm]`**

Parse multiple statements efficiently.

- **Parameters**:
  - `texts`: List of statements
  - `context_id`: Context identifier
  - `use_cache`: Whether to use cache

- **Returns**: List of `LogicalForm` objects

---

**`switch_provider(provider_name: str, model: Optional[str] = None, api_key: Optional[str] = None) -> None`**

Switch to different LLM provider.

- **Parameters**:
  - `provider_name`: New provider name
  - `model`: Optional model override
  - `api_key`: Optional API key

---

**`clear_cache() -> int`**

Clear parsing cache.

- **Returns**: Number of entries cleared

---

**`get_cache_stats() -> Dict[str, Any]`**

Get cache statistics.

- **Returns**: Dictionary with cache info

---

## Best Practices

### ✅ DO

- Use Ollama for development (free, fast, offline)
- Enable caching to reduce costs
- Use batch processing for multiple statements
- Check confidence scores for quality control
- Switch to cloud models for production accuracy
- Handle low-confidence parses gracefully

### ❌ DON'T

- Don't disable caching unless necessary
- Don't use expensive models for simple statements
- Don't parse non-logical text (questions, greetings)
- Don't ignore confidence scores
- Don't use default timeouts for all use cases

---

## What's Next?

After parsing with `LLMLogicalParser`:

1. **Add Embeddings**: Use `SemanticEncoder` to add 768-dim vectors
2. **Check Consistency**: Use `ConsistencyChecker` to detect contradictions
3. **Store in Memory**: Use `MemoryManager` to store in ChromaDB
4. **Search Similar**: Use embeddings for semantic search

**See**: `AdvancedGLCS` wrapper for complete pipeline integration.

---

**Last Updated**: Stage 1.5 Implementation
**Version**: 1.0.0
