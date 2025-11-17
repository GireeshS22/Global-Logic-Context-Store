# GLCS Utils Module

The `utils` module provides foundational utilities used throughout the GLCS system.

## Components

### 1. Configuration Manager (`config_manager.py`)

**Purpose**: Load, validate, and access configuration parameters from YAML files.

**Key Functions**:

#### `load_config(config_path) → dict`
Load configuration from YAML file.

```python
from glcs.utils.config_manager import load_config

config = load_config("config/glcs_config.yaml")
print(config['memory']['vector_dimension'])  # 768
```

**Features**:
- ✅ Automatic path resolution (handles relative paths)
- ✅ YAML validation
- ✅ Schema validation (required sections, value ranges)
- ✅ Clear error messages

**Raises**:
- `FileNotFoundError` - Config file doesn't exist
- `yaml.YAMLError` - Invalid YAML syntax
- `ConfigurationError` - Validation failure

---

#### `validate_config(config) → bool`
Validate configuration structure and values.

```python
from glcs.utils.config_manager import validate_config

try:
    validate_config(config)
    print("Configuration is valid!")
except ConfigurationError as e:
    print(f"Invalid config: {e}")
```

**Checks**:
- Required sections present (`memory`, `consistency`, `encoder`, `parser`, `logging`)
- Value ranges (e.g., thresholds are 0.0-1.0)
- Type correctness
- Compatibility (e.g., vector_dimension matches encoder model)

---

#### `get_config_value(config, path, default) → Any`
Get nested configuration value using dot notation.

```python
from glcs.utils.config_manager import get_config_value

# Access nested values
threshold = get_config_value(config, "memory.similarity_threshold")

# With default
timeout = get_config_value(config, "parser.timeout", default=30)
```

**Path Examples**:
- `"memory.vector_dimension"` → `config['memory']['vector_dimension']`
- `"encoder.model_name"` → `config['encoder']['model_name']`
- `"nonexistent.path"` → returns `default`

---

#### `load_config_with_env_overrides(config_path) → dict`
Load configuration with environment variable overrides.

```python
import os
from glcs.utils.config_manager import load_config_with_env_overrides

os.environ['GLCS_LOG_LEVEL'] = 'DEBUG'
config = load_config_with_env_overrides("config/glcs_config.yaml")

print(config['logging']['level'])  # 'DEBUG' (overridden)
```

**Supported Environment Variables**:
- `GLCS_LOG_LEVEL` → `logging.level`
- `GLCS_MEMORY_PATH` → `memory.storage_path`

---

#### `save_config(config, config_path) → None`
Save configuration to YAML file.

```python
from glcs.utils.config_manager import save_config

# Modify config
config['memory']['similarity_threshold'] = 0.90

# Save
save_config(config, "config/glcs_config_modified.yaml")
```

---

### 2. Logger (`logger.py`)

**Purpose**: Centralized logging configuration and logger instances.

**Key Functions**:

#### `setup_logging(config_path) → None`
Initialize logging from YAML configuration file.

```python
from glcs.utils.logger import setup_logging

# Set up logging (call once at app startup)
setup_logging("config/logging.yaml")
```

**Note**: Usually you don't need to call this explicitly - `get_logger()` auto-configures.

---

#### `get_logger(name, level) → logging.Logger`
Get a configured logger instance.

```python
from glcs.utils.logger import get_logger

# In each module:
logger = get_logger(__name__)

# Log at different levels
logger.debug("Detailed debug info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical failure")
```

**Best Practice**: Always use `__name__` as the logger name for proper module tracking.

**With level override**:
```python
# Force DEBUG level for this logger
debug_logger = get_logger(__name__, level="DEBUG")
```

---

#### `reset_logging() → None`
Reset logging configuration (useful for testing).

```python
from glcs.utils.logger import reset_logging

# Reset logging
reset_logging()

# Reconfigure with different settings
setup_logging("config/logging_test.yaml")
```

---

### 3. Exceptions (`exceptions.py`)

**Purpose**: Custom exception hierarchy for specific GLCS errors.

**Exception Hierarchy**:

```
GLCSException (base)
├── ConfigurationError      # Configuration issues
├── MemoryError            # Memory operations failures
├── ConsistencyError       # Consistency checking failures
├── ValidationError        # Data validation failures
└── ParsingError           # Parsing failures
```

---

#### When to Use Each Exception

**`ConfigurationError`** - Configuration problems
```python
from glcs.utils.exceptions import ConfigurationError

if 'memory' not in config:
    raise ConfigurationError("Missing 'memory' section in configuration")

if threshold > 1.0:
    raise ConfigurationError(
        f"Threshold {threshold} out of range [0.0, 1.0]"
    )
```

**`MemoryError`** - Memory operations fail
```python
from glcs.utils.exceptions import MemoryError

if vector.shape[0] != self.vector_dim:
    raise MemoryError(
        f"Vector dimension mismatch: expected {self.vector_dim}, "
        f"got {vector.shape[0]}"
    )

if not self._can_write():
    raise MemoryError("Memory full and eviction failed")
```

**`ConsistencyError`** - Consistency checking errors
```python
from glcs.utils.exceptions import ConsistencyError

if logical_form.subject is None:
    raise ConsistencyError(
        "Cannot check consistency: logical form missing subject"
    )
```

**Note**: This is for errors in the checking *process*, not detected contradictions (those go in `ConsistencyReport`).

**`ValidationError`** - Data validation fails
```python
from glcs.utils.exceptions import ValidationError

if context_id is None or context_id == "":
    raise ValidationError("context_id cannot be empty")

if not isinstance(polarity, Polarity):
    raise ValidationError(
        f"polarity must be Polarity enum, got {type(polarity)}"
    )
```

**`ParsingError`** - Parsing fails
```python
from glcs.utils.exceptions import ParsingError

if api_response.status_code != 200:
    raise ParsingError(
        f"LLM API failed with status {api_response.status_code}"
    )

if not is_valid_json(llm_output):
    raise ParsingError(f"LLM returned invalid JSON: {llm_output}")
```

---

#### Catching GLCS Exceptions

**Catch specific exception**:
```python
from glcs.utils.exceptions import ConfigurationError

try:
    config = load_config("config.yaml")
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    # Handle config-specific error
```

**Catch any GLCS exception**:
```python
from glcs.utils.exceptions import GLCSException

try:
    result = glcs.process_statement(text)
except GLCSException as e:
    logger.error(f"GLCS operation failed: {e}")
    # Handle any GLCS error
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle non-GLCS errors
```

---

#### `format_exception_message(exception, context, suggestions) → str`
Format exception with context and suggestions.

```python
from glcs.utils.exceptions import format_exception_message

try:
    config = load_config("missing.yaml")
except FileNotFoundError as e:
    msg = format_exception_message(
        e,
        context="Loading GLCS configuration",
        suggestions=[
            "Check that config/glcs_config.yaml exists",
            "Copy from template: cp config/glcs_config.yaml.template config/glcs_config.yaml"
        ]
    )
    print(msg)
```

**Output**:
```
[FileNotFoundError] Configuration file not found: missing.yaml

Context: Loading GLCS configuration

Suggestions:
  - Check that config/glcs_config.yaml exists
  - Copy from template: cp config/glcs_config.yaml.template config/glcs_config.yaml
```

---

## Usage Patterns

### Pattern 1: Component Initialization

**Every GLCS component should**:

```python
from glcs.utils.config_manager import load_config
from glcs.utils.logger import get_logger

class MyComponent:
    def __init__(self, config_path="config/glcs_config.yaml"):
        # Get logger (module-specific)
        self.logger = get_logger(__name__)

        # Load configuration
        self.config = load_config(config_path)

        # Extract component-specific config
        self.my_config = self.config.get('my_component', {})

        self.logger.info("MyComponent initialized")
```

---

### Pattern 2: Error Handling

**Raise specific exceptions, catch appropriately**:

```python
from glcs.utils.exceptions import ValidationError, MemoryError
from glcs.utils.logger import get_logger

logger = get_logger(__name__)

def process(data):
    # Validate input
    if data is None:
        raise ValidationError("Data cannot be None")

    # Try operation
    try:
        result = memory.write(data)
    except MemoryError as e:
        logger.error(f"Failed to write to memory: {e}")
        raise  # Re-raise if unrecoverable

    return result
```

---

### Pattern 3: Configuration Access

**Use get_config_value for safe nested access**:

```python
from glcs.utils.config_manager import load_config, get_config_value

config = load_config("config/glcs_config.yaml")

# Safe nested access with defaults
threshold = get_config_value(
    config,
    "consistency.direct_contradiction_threshold",
    default=0.85
)

# Direct access (will KeyError if missing)
# threshold = config['consistency']['direct_contradiction_threshold']  # ❌ Risky
```

---

## Testing

All utils have comprehensive unit tests in `tests/unit/`:

- `test_config_manager.py` - Config loading, validation
- `test_logger.py` - Logger initialization, output
- `test_exceptions.py` - Exception raising, catching

Run tests:
```bash
poetry run pytest tests/unit/test_config_manager.py -v
poetry run pytest tests/unit/test_logger.py -v
poetry run pytest tests/unit/test_exceptions.py -v
```

---

## Dependencies

**Required**:
- `pyyaml` - YAML parsing (config files)
- `logging` - Python standard library (logging)

**No external dependencies** for exceptions (pure Python).

---

## Best Practices

1. **Always use get_logger(__name__)**
   ```python
   logger = get_logger(__name__)  # ✅ Module-specific logger
   logger = logging.getLogger()    # ❌ Generic logger
   ```

2. **Load config once, pass to components**
   ```python
   # At app startup
   config = load_config("config/glcs_config.yaml")

   # Pass to components
   encoder = SemanticEncoder(config=config['encoder'])
   memory = MemoryManager(config=config['memory'])
   ```

3. **Use specific exceptions**
   ```python
   raise ConfigurationError("Specific error")  # ✅
   raise Exception("Something went wrong")     # ❌
   ```

4. **Catch specific exceptions first**
   ```python
   try:
       operation()
   except ConfigurationError as e:  # ✅ Specific first
       handle_config_error(e)
   except GLCSException as e:
       handle_glcs_error(e)
   except Exception as e:
       handle_generic_error(e)
   ```

5. **Don't suppress exceptions without logging**
   ```python
   try:
       risky_operation()
   except Exception as e:
       logger.error(f"Operation failed: {e}")  # ✅ Log before ignoring
       pass

   # DON'T DO THIS:
   try:
       risky_operation()
   except Exception:
       pass  # ❌ Silent failure
   ```

---

## Files in This Module

- `config_manager.py` - Configuration utilities ✅
- `logger.py` - Logging utilities ✅
- `exceptions.py` - Custom exceptions ✅
- `README.md` - This file ✅

---

**Last Updated**: Stage 0.2 (Configuration System)
