# Getting Started with GLCS

Welcome to GLCS (Global Logical Context Store)! This guide will help you get up and running quickly.

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Step 1: Clone the Repository

```bash
git clone https://github.com/GireeshS22/Global-Logic-Context-Store.git
cd Global-Logic-Context-Store
```

### Step 2: Create a Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install in development mode:

```bash
pip install -e .
```

### Step 4: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key (if using the LLM wrapper):

```
OPENAI_API_KEY=your_api_key_here
GLCS_LOG_LEVEL=INFO
GLCS_MEMORY_PATH=glcs_memory.json
```

## Quick Start

### Basic Usage

Here's a simple example to get you started:

```python
from glcs import SimpleParser, SimpleMemory, ConsistencyChecker

# Initialize components
parser = SimpleParser()
memory = SimpleMemory()
checker = ConsistencyChecker(memory)

# Parse a statement
statement = parser.parse("All birds can fly")
print(f"Parsed: {statement}")

# Check consistency and store
is_consistent, confidence, violations = checker.check_consistency(statement)

if is_consistent:
    memory.store(statement)
    print("Statement stored!")
else:
    print(f"Violations: {violations}")

# Try a contradictory statement
contradiction = parser.parse("Penguins cannot fly")
is_consistent, confidence, violations = checker.check_consistency(contradiction)

if not is_consistent:
    print(f"Contradiction detected! {violations}")
```

### Using the LLM Wrapper

If you want to integrate GLCS with OpenAI's API:

```python
from glcs import GLCSWrapper

# Initialize wrapper (requires OPENAI_API_KEY in environment)
glcs = GLCSWrapper()

# Generate a response with consistency checking
result = glcs.generate("Tell me about birds that can fly")
print(result['response'])

# Check if response was consistent
if not result['consistent']:
    print(f"Violations: {result['violations']}")

# View memory summary
summary = glcs.get_memory_summary()
print(f"Stored {summary['statistics']['total']} facts")
```

## Running the Demo

### Command-Line Demo

Run the basic demo to see GLCS in action:

```bash
python examples/basic_demo.py
```

This will demonstrate:
- Parsing logical statements
- Storing facts in memory
- Detecting contradictions
- Querying stored knowledge

### Streamlit Web App

Launch the interactive web demo:

```bash
streamlit run examples/streamlit_app.py
```

Then open your browser to http://localhost:8501

The web app lets you:
- Enter statements interactively
- See real-time contradiction detection
- Browse your knowledge base
- Visualize stored facts

## Running Tests

Run the test suite to verify everything is working:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_parser.py

# Run with coverage report
pytest --cov=glcs tests/
```

## Core Concepts

### Logical Statement Types

GLCS recognizes three types of logical statements:

1. **Universal Rules**: Statements about all members of a category
   - "All birds can fly"
   - "Every employee has benefits"
   - "No fish can walk"

2. **Conditional Rules**: If-then relationships
   - "If a server crashes then it restarts"
   - "When an employee joins they receive training"

3. **Ground Facts**: Specific facts about individuals
   - "John is a manager"
   - "Mary has a degree"
   - "Server1 can restart"

### How It Works

1. **Parsing**: Text is parsed into structured logical statements
2. **Checking**: New statements are checked against stored knowledge
3. **Storage**: Consistent statements are stored in memory
4. **Querying**: You can query stored knowledge by subject or type

### Memory Persistence

GLCS automatically saves your knowledge base to disk:

```python
# Memory is saved to glcs_memory.json by default
memory = SimpleMemory(persist_path="my_memory.json")

# Clear all stored knowledge
memory.clear()

# Get statistics
stats = memory.get_stats()
print(f"Total facts: {stats['total']}")
```

## Next Steps

- Read the [API Reference](api_reference.md) for detailed documentation
- Check out the examples in the `examples/` directory
- Run the tests to see more usage patterns
- Contribute to the project on [GitHub](https://github.com/GireeshS22/Global-Logic-Context-Store)

## Troubleshooting

### "Module not found" errors

Make sure you've installed the dependencies:
```bash
pip install -r requirements.txt
```

### OpenAI API errors

- Check that your API key is set in `.env`
- Verify you have credits in your OpenAI account
- The LLM wrapper is optional - you can use GLCS without it

### Test failures

If tests fail on first run:
```bash
# Make sure you're in the project root
cd Global-Logic-Context-Store

# Install in development mode
pip install -e .

# Run tests again
pytest
```

## Getting Help

- Check the [API Reference](api_reference.md)
- Look at examples in `examples/`
- Review test cases in `tests/`
- Open an issue on [GitHub](https://github.com/GireeshS22/Global-Logic-Context-Store/issues)
