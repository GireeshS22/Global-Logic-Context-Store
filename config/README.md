# GLCS Configuration

This directory contains all configuration files for the Global Logical Context Store.

## Configuration Files

### 1. `glcs_config.yaml` - Main Configuration

The primary configuration file for all GLCS parameters.

**Sections**:

#### Memory Configuration
```yaml
memory:
  vector_dimension: 768          # Must match encoder model output
  similarity_threshold: 0.85     # For retrieving related statements (0.0-1.0)
  initial_capacity: 1000         # Initial memory hint (grows dynamically)
```

**Parameters**:
- `vector_dimension`: **CRITICAL** - Must match encoder model
  - 384 for `all-MiniLM-L6-v2` base
  - 768 for `all-mpnet-base-v2` (default)
  - **Changing this requires re-encoding all data**

- `similarity_threshold`: Higher = stricter matching
  - 0.85 = high similarity required (recommended for contradiction detection)
  - 0.70 = medium similarity (more recall, less precision)
  - Tune based on false positive/negative rate

- `initial_capacity`: Performance hint, not a hard limit
  - Memory grows dynamically beyond this

#### Consistency Configuration
```yaml
consistency:
  direct_contradiction_threshold: 0.85   # Similarity for contradiction check
  confidence_threshold: 0.5              # Min confidence to report violation
```

**Parameters**:
- `direct_contradiction_threshold`: Similarity needed to check for contradiction
  - Should match or be close to `memory.similarity_threshold`

- `confidence_threshold`: Lower = more sensitive (more false positives)
  - 0.5 = medium sensitivity (balanced)
  - 0.7 = high confidence required (fewer false positives)

#### Encoder Configuration
```yaml
encoder:
  model_name: "sentence-transformers/all-MiniLM-L6-v2"
  batch_size: 32
  cache_embeddings: true
```

**Parameters**:
- `model_name`: Sentence-transformer model to use
  - `all-MiniLM-L6-v2` - Fast, 384-dim (good for MVP)
  - `all-mpnet-base-v2` - Better quality, 768-dim (recommended)
  - **WARNING**: Changing model requires updating `memory.vector_dimension`

- `batch_size`: Statements to encode in one batch
  - Higher = faster but more memory
  - 32 is a good default

- `cache_embeddings`: Whether to cache encoded vectors
  - `true` = faster repeated encoding, uses memory
  - `false` = slower but no caching overhead

#### Parser Configuration
```yaml
parser:
  llm_provider: "openai"
  model: "gpt-4o-mini"
  max_retries: 3
  timeout: 30
  cache_enabled: true
```

**Parameters**:
- `llm_provider`: LLM API provider
  - `openai` - Currently supported
  - `anthropic`, `google` - Future support

- `model`: Specific LLM model
  - `gpt-4o-mini` - Cheap, fast (recommended for MVP)
  - `gpt-4o` - Better quality, more expensive
  - `gpt-4-turbo` - Fast, high quality

- `max_retries`: API failure retries (3 is recommended)

- `timeout`: Request timeout in seconds

- `cache_enabled`: Cache parsing results
  - `true` = much faster for repeated statements
  - Recommended: `true`

#### Logging Configuration
```yaml
logging:
  level: "INFO"
  format: "simple"
  log_file: "glcs.log"
```

**Parameters**:
- `level`: Minimum log level
  - `DEBUG` - Verbose, development only
  - `INFO` - Normal operations (recommended)
  - `WARNING` - Only warnings and errors
  - `ERROR` - Only errors

- `format`: Log message format
  - `simple` - Human-readable (for development)
  - `json` - Structured (for production/parsing)

---

### 2. `logging.yaml` - Detailed Logging Configuration

Python logging configuration using `dictConfig` schema.

**Structure**:
```yaml
formatters:  # How log messages are formatted
  simple: Human-readable
  detailed: With file and line numbers
  json: Machine-readable structured format

handlers:    # Where logs go
  console: Standard output
  file: glcs.log (JSON format)
  error_file: glcs_errors.log (errors only)

loggers:     # Module-specific logging
  glcs: All GLCS modules
  glcs.core.consistency_checker: Specific module override
```

**Customization**:
- Add new formatters in `formatters` section
- Add new handlers (e.g., syslog, email) in `handlers`
- Configure specific modules in `loggers`

---

## How to Modify Configuration

### Option 1: Edit YAML Files Directly

1. Open `config/glcs_config.yaml`
2. Modify parameters
3. Save and restart GLCS

**Example** - Change log level:
```yaml
logging:
  level: "DEBUG"  # Changed from INFO
```

### Option 2: Environment Variable Overrides

Set environment variables to override config:

```bash
export GLCS_CONFIG_PATH=/custom/path/to/config.yaml
export GLCS_LOG_LEVEL=DEBUG
```

**Supported Environment Variables**:
- `GLCS_CONFIG_PATH` - Override config file location
- `GLCS_LOG_LEVEL` - Override log level
- `GLCS_MEMORY_PATH` - Override memory storage path

### Option 3: Programmatic Configuration

```python
from glcs.utils.config_manager import load_config

# Load config
config = load_config("config/glcs_config.yaml")

# Modify in code
config['memory']['similarity_threshold'] = 0.90

# Pass to components
memory_manager = MemoryManager(config=config)
```

---

## Configuration Validation

The config manager validates:
- ✅ All required sections present
- ✅ Value ranges (e.g., thresholds are 0.0-1.0)
- ✅ Type correctness (int, float, str, bool)
- ⚠️ Compatibility warnings (e.g., vector_dimension mismatch)

**Invalid config raises**: `ConfigurationError`

---

## Common Configuration Scenarios

### Scenario 1: Optimize for Speed
```yaml
encoder:
  model_name: "all-MiniLM-L6-v2"  # Faster model
  batch_size: 64                   # Larger batches
  cache_embeddings: true

memory:
  vector_dimension: 384            # Match model
  similarity_threshold: 0.80       # Slightly lower for speed
```

### Scenario 2: Optimize for Accuracy
```yaml
encoder:
  model_name: "all-mpnet-base-v2"  # Better model
  batch_size: 16                    # Smaller batches (more stable)

memory:
  vector_dimension: 768             # Match model
  similarity_threshold: 0.90        # Stricter matching

consistency:
  direct_contradiction_threshold: 0.90
  confidence_threshold: 0.7         # Higher confidence required
```

### Scenario 3: Development/Debugging
```yaml
logging:
  level: "DEBUG"
  format: "detailed"

parser:
  model: "gpt-4o-mini"  # Cheap for testing
  cache_enabled: true   # Avoid repeated API calls
```

### Scenario 4: Production Deployment
```yaml
logging:
  level: "INFO"
  format: "json"

parser:
  model: "gpt-4o"       # Better quality
  max_retries: 5        # More resilient
  timeout: 60           # Longer timeout

encoder:
  cache_embeddings: false  # Avoid memory bloat
```

---

## Configuration Versioning

**Current Version**: 0.1.0 (MVP)

When config schema changes:
1. Version number will increment
2. Migration scripts provided
3. Backward compatibility maintained for 1 version

**Future**: Config versioning field will be added to track schema version.

---

## Troubleshooting

### Issue: "ConfigurationError: Missing section 'memory'"
**Solution**: Ensure config file has all required sections. Compare with default `glcs_config.yaml`.

### Issue: "Vector dimension mismatch"
**Solution**: `memory.vector_dimension` must match encoder model output:
- `all-MiniLM-L6-v2` → 384
- `all-mpnet-base-v2` → 768

### Issue: Logs not appearing
**Solution**: Check `logging.level` in config. Set to `DEBUG` for verbose output.

### Issue: Parser API timeout
**Solution**: Increase `parser.timeout` or reduce `parser.max_retries`.

---

## Best Practices

1. **Don't hardcode parameters** - Always use config files
2. **Use environment variables for secrets** - Never commit API keys to config
3. **Version control config changes** - Track why parameters changed
4. **Test config changes** - Run tests after modifying config
5. **Document custom values** - Add comments explaining non-default values

---

## Files in This Directory

- `glcs_config.yaml` - Main GLCS configuration ✅
- `logging.yaml` - Logging configuration ✅
- `README.md` - This file ✅

---

**Last Updated**: Stage 0.2 (Configuration System)
