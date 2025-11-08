# GLCS API Reference

Complete API documentation for all GLCS components.

## Core Module (`glcs.core`)

### LogicalType

```python
class LogicalType(Enum):
    UNIVERSAL = "universal"
    CONDITIONAL = "conditional"
    GROUND = "ground"
```

Enumeration of supported logical statement types.

**Values:**
- `UNIVERSAL`: Statements about all members of a category (e.g., "All X are Y")
- `CONDITIONAL`: If-then relationships (e.g., "If X then Y")
- `GROUND`: Specific facts about individuals (e.g., "John is X")

### LogicalStatement

```python
@dataclass
class LogicalStatement:
    type: LogicalType
    subject: str
    predicate: str
    object: Optional[str] = None
    confidence: float = 0.9
    raw_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
```

Represents a parsed logical statement.

**Attributes:**
- `type`: The type of logical statement
- `subject`: The subject of the statement
- `predicate`: The predicate describing the subject
- `object`: Optional object for conditional statements
- `confidence`: Confidence score (0-1) for this statement
- `raw_text`: Original text that was parsed
- `metadata`: Additional metadata about the statement

**Methods:**

#### `contradicts(other: LogicalStatement) -> bool`

Check if this statement contradicts another statement.

**Parameters:**
- `other`: Another logical statement to check against

**Returns:**
- `True` if the statements contradict each other, `False` otherwise

**Example:**
```python
stmt1 = LogicalStatement(type=LogicalType.GROUND, subject="john", predicate="is_manager")
stmt2 = LogicalStatement(type=LogicalType.GROUND, subject="john", predicate="is_engineer")
print(stmt1.contradicts(stmt2))  # True (mutually exclusive predicates)
```

---

## Parser Module (`glcs.parser`)

### SimpleParser

```python
class SimpleParser:
    def __init__(self)
    def parse(self, text: str) -> Optional[LogicalStatement]
    def extract_statements(self, text: str) -> List[LogicalStatement]
    def add_pattern(self, logical_type: str, pattern: str)
```

Rule-based parser for extracting logical statements from natural language.

**Methods:**

#### `parse(text: str) -> Optional[LogicalStatement]`

Parse text into a logical statement.

**Parameters:**
- `text`: The text to parse

**Returns:**
- A `LogicalStatement` if a pattern matches, `None` otherwise

**Example:**
```python
parser = SimpleParser()
stmt = parser.parse("All birds can fly")
print(stmt.type)  # LogicalType.UNIVERSAL
print(stmt.subject)  # "birds"
print(stmt.predicate)  # "is_fly"
```

#### `extract_statements(text: str) -> List[LogicalStatement]`

Extract all logical statements from text.

**Parameters:**
- `text`: The text to extract statements from

**Returns:**
- A list of `LogicalStatement` objects found in the text

**Example:**
```python
text = "All birds can fly. John is a bird. Mary has wings."
statements = parser.extract_statements(text)
print(len(statements))  # 3
```

#### `add_pattern(logical_type: str, pattern: str)`

Add a custom pattern for parsing.

**Parameters:**
- `logical_type`: One of 'universal', 'conditional', or 'ground'
- `pattern`: A regex pattern with appropriate capture groups

**Example:**
```python
parser.add_pattern('universal', r'always (\w+) are (\w+)')
stmt = parser.parse("always cats are mammals")
```

---

## Memory Module (`glcs.memory`)

### SimpleMemory

```python
class SimpleMemory:
    def __init__(self, persist_path: Optional[str] = "glcs_memory.json")
    def store(self, statement: LogicalStatement) -> bool
    def find_conflicts(self, statement: LogicalStatement) -> List[LogicalStatement]
    def query(self, subject: Optional[str] = None, type: Optional[LogicalType] = None) -> List[LogicalStatement]
    def save(self)
    def load(self)
    def clear(self)
    def get_stats(self) -> Dict[str, int]
```

Dictionary-based memory store for logical statements with disk persistence.

**Methods:**

#### `__init__(persist_path: Optional[str] = "glcs_memory.json")`

Initialize the memory store.

**Parameters:**
- `persist_path`: Path to JSON file for persistence. `None` to disable persistence.

#### `store(statement: LogicalStatement) -> bool`

Store a logical statement.

**Parameters:**
- `statement`: The statement to store

**Returns:**
- `True` if stored successfully, `False` if contradictions were found

**Example:**
```python
memory = SimpleMemory()
stmt = LogicalStatement(type=LogicalType.GROUND, subject="john", predicate="is_manager")
success = memory.store(stmt)
```

#### `find_conflicts(statement: LogicalStatement) -> List[LogicalStatement]`

Find statements that conflict with the given one.

**Parameters:**
- `statement`: The statement to check for conflicts

**Returns:**
- List of conflicting statements

#### `query(subject: Optional[str] = None, type: Optional[LogicalType] = None) -> List[LogicalStatement]`

Query memory for relevant statements.

**Parameters:**
- `subject`: Filter by subject (optional)
- `type`: Filter by logical type (optional)

**Returns:**
- List of matching statements

**Example:**
```python
# Get all facts about John
john_facts = memory.query(subject="john")

# Get all universal rules
universals = memory.query(type=LogicalType.UNIVERSAL)

# Get universal rules about birds
bird_universals = memory.query(subject="birds", type=LogicalType.UNIVERSAL)
```

#### `clear()`

Clear all stored knowledge.

#### `get_stats() -> Dict[str, int]`

Get statistics about stored statements.

**Returns:**
- Dictionary with counts for each statement type

**Example:**
```python
stats = memory.get_stats()
print(f"Total: {stats['total']}")
print(f"Universal: {stats['universal']}")
print(f"Ground: {stats['ground']}")
```

---

## Checker Module (`glcs.checker`)

### ConsistencyChecker

```python
class ConsistencyChecker:
    def __init__(self, memory: SimpleMemory)
    def check_consistency(self, statement: LogicalStatement) -> Tuple[bool, float, List[str]]
    def suggest_alternative(self, statement: LogicalStatement, violations: List[str]) -> Optional[str]
    def get_supporting_facts(self, statement: LogicalStatement) -> List[LogicalStatement]
    def verify_knowledge_base(self) -> Tuple[bool, List[str]]
```

Check logical consistency of statements against stored knowledge.

**Methods:**

#### `check_consistency(statement: LogicalStatement) -> Tuple[bool, float, List[str]]`

Check if statement is consistent with memory.

**Parameters:**
- `statement`: The statement to check

**Returns:**
- Tuple of `(is_consistent, confidence_score, violations)`
  - `is_consistent`: True if no contradictions found
  - `confidence_score`: Confidence in the consistency check (0-1)
  - `violations`: List of human-readable violation messages

**Example:**
```python
checker = ConsistencyChecker(memory)
stmt = parser.parse("Penguins cannot fly")
is_consistent, confidence, violations = checker.check_consistency(stmt)

if not is_consistent:
    print(f"Violations: {violations}")
```

#### `suggest_alternative(statement: LogicalStatement, violations: List[str]) -> Optional[str]`

Suggest alternative phrasing that would be consistent.

**Parameters:**
- `statement`: The statement that has violations
- `violations`: List of violations found

**Returns:**
- A suggestion string, or `None` if no suggestion available

#### `get_supporting_facts(statement: LogicalStatement) -> List[LogicalStatement]`

Get facts that support or relate to the given statement.

**Parameters:**
- `statement`: The statement to find support for

**Returns:**
- List of related statements

#### `verify_knowledge_base() -> Tuple[bool, List[str]]`

Verify the entire knowledge base for internal consistency.

**Returns:**
- Tuple of `(is_consistent, list of inconsistencies found)`

**Example:**
```python
is_consistent, inconsistencies = checker.verify_knowledge_base()
if not is_consistent:
    for inc in inconsistencies:
        print(f"Problem: {inc}")
```

---

## LLM Wrapper Module (`glcs.llm_wrapper`)

### GLCSWrapper

```python
class GLCSWrapper:
    def __init__(self, api_key: Optional[str] = None, memory_path: Optional[str] = None, model: str = "gpt-3.5-turbo")
    def generate(self, prompt: str, check_consistency: bool = True, max_tokens: int = 150, temperature: float = 0.7) -> Dict[str, Any]
    def verify_statement(self, statement: str) -> Dict[str, Any]
    def get_memory_summary(self) -> Dict[str, Any]
    def clear_memory(self)
    def reset_conversation(self)
    def verify_knowledge_base(self) -> Dict[str, Any]
```

Wrapper for OpenAI API with GLCS consistency checking.

**Methods:**

#### `__init__(api_key: Optional[str] = None, memory_path: Optional[str] = None, model: str = "gpt-3.5-turbo")`

Initialize the GLCS wrapper.

**Parameters:**
- `api_key`: OpenAI API key (defaults to `OPENAI_API_KEY` env var)
- `memory_path`: Path for memory persistence
- `model`: OpenAI model to use

#### `generate(prompt: str, check_consistency: bool = True, max_tokens: int = 150, temperature: float = 0.7) -> Dict[str, Any]`

Generate response with optional consistency checking.

**Parameters:**
- `prompt`: User prompt
- `check_consistency`: Whether to check consistency
- `max_tokens`: Maximum tokens in response
- `temperature`: Sampling temperature

**Returns:**
- Dictionary with response and metadata:
  ```python
  {
      'prompt': str,
      'response': str,
      'consistent': bool,
      'violations': List[str],
      'memory_stats': Dict[str, int]
  }
  ```

**Example:**
```python
glcs = GLCSWrapper()
result = glcs.generate("Tell me about birds")

print(result['response'])
if not result['consistent']:
    print(f"Warning: {result['violations']}")
```

#### `verify_statement(statement: str) -> Dict[str, Any]`

Verify a statement against stored knowledge.

**Parameters:**
- `statement`: Statement to verify

**Returns:**
- Dictionary with verification results:
  ```python
  {
      'statement': str,
      'parsed': bool,
      'consistent': bool,
      'confidence': float,
      'violations': List[str],
      'supporting_facts': List[str]
  }
  ```

#### `get_memory_summary() -> Dict[str, Any]`

Get a summary of stored knowledge.

**Returns:**
- Dictionary with memory statistics and samples

#### `clear_memory()`

Clear all stored knowledge and conversation history.

#### `reset_conversation()`

Reset conversation history but keep memory.

---

## Usage Examples

### Complete Workflow Example

```python
from glcs import SimpleParser, SimpleMemory, ConsistencyChecker

# Initialize
parser = SimpleParser()
memory = SimpleMemory(persist_path="my_knowledge.json")
checker = ConsistencyChecker(memory)

# Process statements
statements = [
    "All birds can fly",
    "Sparrows are birds",
    "John has a sparrow"
]

for text in statements:
    stmt = parser.parse(text)
    if stmt:
        is_consistent, confidence, violations = checker.check_consistency(stmt)

        if is_consistent:
            memory.store(stmt)
            print(f"✓ Stored: {text}")
        else:
            print(f"✗ Rejected: {text}")
            for v in violations:
                print(f"  - {v}")

# Query knowledge
print("\nAll stored facts:")
for fact in memory.query():
    print(f"- {fact.raw_text}")
```

### With OpenAI Integration

```python
from glcs import GLCSWrapper

# Initialize with API key
glcs = GLCSWrapper(api_key="your-api-key-here")

# Have a conversation
prompts = [
    "All employees get health benefits",
    "John is an employee",
    "Does John get health benefits?"
]

for prompt in prompts:
    result = glcs.generate(prompt)
    print(f"Q: {prompt}")
    print(f"A: {result['response']}")
    print()

# Check memory
summary = glcs.get_memory_summary()
print(f"Knowledge base has {summary['statistics']['total']} facts")
```
