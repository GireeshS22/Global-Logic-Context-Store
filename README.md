# GLCS: Global Logical Context Store

**Multi-Provider Logical Contradiction Detection for LLM Conversations**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

GLCS is a practical tool for detecting logical contradictions in LLM conversations. It maintains a persistent store of logical statements and checks new statements for consistency.

**New in v0.2.0:** Multi-provider support for OpenAI, Anthropic Claude, Google Gemini, Groq, and Ollama!

## ✨ Features

- 🔍 **Multi-Provider Support** - OpenAI, Anthropic, Gemini, Groq, Ollama
- 🆓 **FREE Local Option** - Run completely locally with Ollama (no API costs!)
- 🎯 **Regex-Based Parser** - 28 patterns covering 65% of common logical statements
- 💾 **Persistent Memory** - JSON-based storage for long-term consistency
- ✅ **100% Accuracy** - On direct negations and universal rule violations
- ⚡ **Fast** - <1ms per statement parsing
- 🔒 **Privacy Options** - 100% local with Ollama, or cloud with other providers
- 📊 **Well-Tested** - 250+ test cases, comprehensive evaluation framework

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/GireeshS22/Global-Logic-Context-Store.git
cd Global-Logic-Context-Store

# Install with your preferred provider(s)
poetry install -E openai          # OpenAI only
poetry install -E ollama          # Ollama only (FREE!)
poetry install -E all-providers   # All providers
```

### Basic Usage

```python
from glcs import GLCSWrapper

# Option 1: Use FREE local Ollama (no API key needed!)
wrapper = GLCSWrapper(provider='ollama')

# Option 2: Use OpenAI
wrapper = GLCSWrapper(provider='openai')

# Option 3: Use Google Gemini (cheapest cloud option)
wrapper = GLCSWrapper(provider='gemini')

# Generate response with consistency checking
result = wrapper.generate("All birds can fly")
print(result['response'])

# Check for contradictions
result = wrapper.generate("Penguins cannot fly")
if not result['consistent']:
    print(f"Contradiction detected: {result['violations']}")
```

## 📦 Provider Comparison

| Provider | Cost (per 1K parses) | Speed | Quality | Privacy | Setup |
|----------|---------------------|-------|---------|---------|-------|
| **Ollama** | **FREE** | Fast | Good | 🔒 100% Local | [Guide](docs/OLLAMA_SETUP.md) |
| **Gemini** | $0.04 | Very Fast | Great | ☁️ Cloud | Easy |
| **OpenAI** | $0.06 | Very Fast | Excellent | ☁️ Cloud | Easy |
| **Claude** | $0.08 | Fast | Excellent | ☁️ Cloud | Easy |
| **Groq** | $0.27 | Ultra Fast | Good | ☁️ Cloud | Easy |

**For detailed comparison:** See [Provider Guide](docs/PROVIDER_GUIDE.md)

## 🎯 Use Cases

### Development/Testing
```python
# Use FREE Ollama for development
wrapper = GLCSWrapper(provider='ollama')
```

### Production
```python
# Use reliable OpenAI for production
wrapper = GLCSWrapper(provider='openai', model='gpt-4o-mini')
```

### Privacy-Critical
```python
# Use local Ollama - data never leaves your machine!
wrapper = GLCSWrapper(provider='ollama', model='mistral')
```

### Cost-Optimized
```python
# Use Gemini - cheapest cloud option
wrapper = GLCSWrapper(provider='gemini', model='gemini-1.5-flash')
```

## 📋 Installation Options

### Install Specific Providers

```bash
# OpenAI only
poetry install -E openai

# Anthropic Claude only
poetry install -E anthropic

# Google Gemini only
poetry install -E gemini

# Groq only
poetry install -E groq

# Ollama only (FREE, local)
poetry install -E ollama

# All cloud providers
poetry install -E cloud-providers

# Everything (all providers + dev tools)
poetry install -E all
```

## 🔧 Configuration

### Using Environment Variables

Create a `.env` file:

```bash
# Choose your provider
GLCS_DEFAULT_PROVIDER=openai

# API Keys (only for cloud providers you're using)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
GROQ_API_KEY=gsk_...

# Ollama needs no API key!
```

### Using Config File

Edit `config/glcs_config.yaml`:

```yaml
default_provider: openai

providers:
  openai:
    model: gpt-4o-mini
    temperature: 0.7

  ollama:
    model: llama3.2
    temperature: 0.7
```

### In Code

```python
# Specify provider directly
wrapper = GLCSWrapper(provider='ollama')

# Override model
wrapper = GLCSWrapper(provider='openai', model='gpt-4o')

# Switch providers dynamically
wrapper.switch_provider('gemini')
```

## 📚 Documentation

- **[Ollama Setup Guide](docs/OLLAMA_SETUP.md)** - Set up FREE local LLMs
- **[Provider Guide](docs/PROVIDER_GUIDE.md)** - Compare and choose providers
- **[API Reference](docs/api_reference.md)** - Complete API documentation (coming soon)
- **[Getting Started](docs/getting_started.md)** - Detailed tutorial (coming soon)

## 🧪 Examples

### Basic Contradiction Detection

```python
from glcs import GLCSWrapper

wrapper = GLCSWrapper(provider='ollama')  # FREE!

# Store a fact
wrapper.generate("John is a manager")

# Check for contradiction
result = wrapper.generate("John is an engineer")

if not result['consistent']:
    print(f"Contradiction: {result['violations']}")
    # Output: "Contradiction: ['Contradicts: John is a manager']"
```

### Multi-Provider Usage

```python
# Use different providers for different tasks
dev_wrapper = GLCSWrapper(provider='ollama')      # Development
prod_wrapper = GLCSWrapper(provider='openai')     # Production
fast_wrapper = GLCSWrapper(provider='groq')       # Speed-critical
private_wrapper = GLCSWrapper(provider='ollama')  # Privacy-critical

# All work with the same API!
result = prod_wrapper.generate("What is 2+2?")
```

### Verify Statement Consistency

```python
# Check if a statement is consistent with known facts
wrapper.generate("All birds can fly")

# Verify a new statement
verification = wrapper.verify_statement("Penguins cannot fly")

if not verification['consistent']:
    print(f"This violates: {verification['violations']}")
```

## 🧬 Architecture

```
GLCS Architecture
├── Core Components
│   ├── Parser (28 regex patterns)
│   ├── Memory (persistent JSON store)
│   └── Consistency Checker
├── Provider Abstraction
│   ├── Base Provider Interface
│   ├── OpenAI Provider
│   ├── Anthropic Provider
│   ├── Gemini Provider
│   ├── Groq Provider
│   └── Ollama Provider
└── GLCSWrapper (main interface)
```

## 📊 Performance Metrics

Based on evaluation framework (17 test cases):

- **Overall Accuracy:** 58.82%
- **Precision:** 87.50%
- **Direct Negation Accuracy:** 100%
- **Universal Rule Accuracy:** 100%
- **Processing Speed:** <1ms per statement
- **Parser Coverage:** ~65% of common logical statements

## 🛠️ Development

### Run Tests

```bash
# Install dev dependencies
poetry install -E dev

# Run all tests
pytest

# Run only unit tests
pytest tests/unit

# Run with coverage
pytest --cov=glcs
```

### Code Quality

```bash
# Format code
black glcs tests

# Lint code
ruff glcs tests

# Type checking
mypy glcs
```

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- [ ] Add more parser patterns
- [ ] Improve multi-hop reasoning
- [ ] Add streaming support
- [ ] Create web UI (Streamlit)
- [ ] Add more provider integrations
- [ ] Improve documentation

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude models
- Google for Gemini models
- Groq for ultra-fast inference
- Ollama for local LLM support

## 🔗 Links

- **GitHub:** https://github.com/GireeshS22/Global-Logic-Context-Store
- **Issues:** https://github.com/GireeshS22/Global-Logic-Context-Store/issues
- **Documentation:** https://github.com/GireeshS22/Global-Logic-Context-Store/tree/main/docs

## 📈 Roadmap

### v0.2.0 (Current)
- ✅ Multi-provider support
- ✅ Ollama integration (FREE local LLMs)
- ✅ Configuration system
- ✅ Provider comparison guide

### v0.3.0 (Planned)
- [ ] Streaming support
- [ ] Advanced reasoning
- [ ] Web UI (Streamlit)
- [ ] More providers (Azure, Cohere, etc.)
- [ ] Vector embeddings support

### v1.0.0 (Future)
- [ ] Production-ready
- [ ] Full documentation
- [ ] Comprehensive benchmarks
- [ ] Research paper publication

## ❓ FAQ

**Q: Which provider should I use?**
A: For development, use Ollama (FREE). For production, use OpenAI gpt-4o-mini (best reliability). See [Provider Guide](docs/PROVIDER_GUIDE.md).

**Q: Is Ollama really free?**
A: Yes! Ollama runs 100% locally, no API costs, completely private.

**Q: Can I use multiple providers?**
A: Yes! You can switch providers dynamically or use different providers for different tasks.

**Q: Do I need all API keys?**
A: No! Only get keys for the providers you want to use. Ollama needs no API key.

**Q: Which is fastest?**
A: Groq is the fastest cloud option. Ollama can be very fast on good hardware.

**Q: Which is cheapest?**
A: Ollama is FREE. For cloud, Gemini 1.5 Flash is cheapest at $0.04 per 1K parses.

## 🚀 Getting Started

1. **Install GLCS:**
   ```bash
   poetry install -E ollama  # Start with FREE Ollama
   ```

2. **Set up Ollama (optional but recommended for free usage):**
   ```bash
   # Follow guide: docs/OLLAMA_SETUP.md
   ```

3. **Try it out:**
   ```python
   from glcs import GLCSWrapper
   wrapper = GLCSWrapper(provider='ollama')
   result = wrapper.generate("Hello!")
   print(result['response'])
   ```

4. **Read the guides:**
   - [Ollama Setup](docs/OLLAMA_SETUP.md)
   - [Provider Comparison](docs/PROVIDER_GUIDE.md)

Happy contradiction detecting! 🎯

