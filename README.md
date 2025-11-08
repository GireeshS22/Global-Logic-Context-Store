# GLCS: Global Logical Context Store

**Build a practical tool that catches 50-70% of logical contradictions in LLM conversations with minimal complexity.**

## 🎯 What is GLCS?

GLCS (Global Logical Context Store) is a lightweight system that helps detect logical contradictions in LLM conversations. It's designed to be practical and useful TODAY, not a perfect logical reasoning system.

## ✨ Features

- **Simple Contradiction Detection**: Catches common logical inconsistencies
- **Memory Persistence**: Remembers facts across conversations
- **OpenAI Integration**: Works seamlessly with GPT models
- **Fast Performance**: <500ms latency for most checks
- **Easy to Use**: Simple API and Streamlit demo

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/GireeshS22/Global-Logic-Context-Store.git
cd Global-Logic-Context-Store

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Configuration

Create a `.env` file with your OpenAI API key:

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Basic Usage

```python
from glcs.llm_wrapper import GLCSWrapper

# Initialize GLCS wrapper
glcs = GLCSWrapper()

# Check a statement for consistency
prompt = "All birds can fly."
result = glcs.generate(prompt)

# Later in the conversation...
prompt2 = "Penguins are birds but cannot fly."
result2 = glcs.generate(prompt2)
# GLCS will detect the contradiction!
```

### Run the Streamlit Demo

```bash
streamlit run examples/streamlit_app.py
```

## 📊 System Architecture

```
User Input
    ↓
OpenAI API
    ↓
Simple Parser (rule-based)
    ↓
GLCS Memory Check
    ├── Level 1: Universal Rules ("All X are Y")
    ├── Level 3: Conditionals ("If X then Y")
    └── Level 4: Ground Facts ("John is X")
    ↓
Consistency Score
    ↓
Response (Original or Modified)
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parser.py

# Run with coverage
pytest --cov=glcs tests/
```

## 📖 Documentation

- [Getting Started Guide](docs/getting_started.md)
- [API Reference](docs/api_reference.md)

## 🎯 Month 1 Deliverables

- ✅ Basic contradiction detection
- ✅ Simple memory storage
- ✅ OpenAI integration
- ✅ Universal vs Ground fact checking
- ✅ If-then reasoning
- ✅ Memory persistence
- ✅ Streamlit demo
- ✅ 50% contradiction catch rate
- ✅ <500ms latency
- ✅ Comprehensive test suite

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Built with practical LLM deployment in mind, focusing on what works today rather than perfect logical reasoning.
