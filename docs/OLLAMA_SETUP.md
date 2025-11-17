# Ollama Setup Guide for GLCS

This guide will help you set up Ollama for use with GLCS. Ollama allows you to run powerful LLMs **100% locally** on your machine - no API keys needed, completely private!

## What is Ollama?

Ollama is a tool that lets you run large language models (LLMs) locally on your computer. Key benefits:

- ✅ **FREE** - No API costs
- ✅ **PRIVATE** - Your data never leaves your machine
- ✅ **FAST** - Local inference, no network latency
- ✅ **OFFLINE** - Works without internet connection (after model download)
- ✅ **POWERFUL** - Supports Llama 3.2, Mistral, Qwen 2.5, and more

## Installation

### macOS

```bash
# Using Homebrew (recommended)
brew install ollama

# Or download from website
# Visit: https://ollama.ai/download
```

### Linux

```bash
# Using curl
curl -fsSL https://ollama.ai/install.sh | sh

# Or manual installation
# Download from: https://ollama.ai/download
```

### Windows

```bash
# Download the installer from:
# https://ollama.ai/download

# Run the installer and follow the prompts
```

## Starting Ollama

After installation, start the Ollama service:

```bash
ollama serve
```

**Note:** On macOS and Windows, Ollama starts automatically in the background. On Linux, you may need to run `ollama serve` manually.

## Downloading Models

Before using a model, you need to download it. Here are the recommended models for GLCS:

### Recommended Models

#### 1. Llama 3.2 (Recommended for most users)
```bash
ollama pull llama3.2
```
- **Size:** ~2GB
- **Quality:** Excellent
- **Speed:** Fast
- **Best for:** General use, good balance of quality and speed

#### 2. Mistral (Great for reasoning)
```bash
ollama pull mistral
```
- **Size:** ~4GB
- **Quality:** Excellent
- **Speed:** Fast
- **Best for:** Logical reasoning, technical content

#### 3. Qwen 2.5 (Multilingual support)
```bash
ollama pull qwen2.5
```
- **Size:** ~4.5GB
- **Quality:** Excellent
- **Speed:** Fast
- **Best for:** Multilingual content, excellent at reasoning

#### 4. Phi-3 (Lightweight option)
```bash
ollama pull phi3
```
- **Size:** ~2GB
- **Quality:** Good
- **Speed:** Very fast
- **Best for:** Resource-constrained systems

### Check Available Models

```bash
# List downloaded models
ollama list

# Get model info
ollama show llama3.2
```

## Configuring GLCS to Use Ollama

### Option 1: Using Environment Variables

Create a `.env` file (copy from `.env.template`):

```bash
# No API key needed for Ollama!
GLCS_DEFAULT_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

### Option 2: Using Configuration File

Edit `config/glcs_config.yaml`:

```yaml
default_provider: ollama

providers:
  ollama:
    endpoint: http://localhost:11434
    model: llama3.2
    temperature: 0.7
    max_tokens: 150
    timeout: 60
```

### Option 3: In Code

```python
from glcs import GLCSWrapper

# Use Ollama provider
wrapper = GLCSWrapper(provider='ollama')

# Or specify model
wrapper = GLCSWrapper(provider='ollama', model='mistral')
```

## Testing Your Setup

Test that Ollama is working correctly:

```python
from glcs import GLCSWrapper

# Create wrapper with Ollama
wrapper = GLCSWrapper(provider='ollama')

# Generate a response
result = wrapper.generate("What is 2 + 2?")
print(result['response'])

# Check provider info
info = wrapper.get_provider_info()
print(f"Using provider: {info['provider']}")
print(f"Model: {info['model']}")
print(f"Privacy: {info['privacy']}")
```

Expected output:
```
4
Using provider: ollama
Model: llama3.2
Privacy: 100% local - no data leaves your machine
```

## Troubleshooting

### "Cannot connect to Ollama"

**Problem:** GLCS can't connect to Ollama

**Solutions:**
1. Make sure Ollama is running: `ollama serve`
2. Check if Ollama is listening on port 11434: `curl http://localhost:11434`
3. Try restarting Ollama

### "Model not found"

**Problem:** Model not available locally

**Solutions:**
1. Pull the model: `ollama pull llama3.2`
2. Check available models: `ollama list`
3. GLCS will automatically try to pull the model if not found

### Slow Performance

**Problem:** Model responses are slow

**Solutions:**
1. Use a smaller model like `phi3`
2. Increase `timeout` in config (default: 60 seconds)
3. Make sure you have enough RAM (8GB minimum recommended)
4. Close other applications to free up memory

### Out of Memory

**Problem:** System runs out of memory

**Solutions:**
1. Use a smaller model: `phi3` (2GB) instead of `llama3.2` (4GB)
2. Close other applications
3. Increase system swap space
4. Consider using a cloud provider for very large models

## Model Comparison

| Model | Size | RAM Needed | Quality | Speed | Best For |
|-------|------|------------|---------|-------|----------|
| llama3.2 | ~2GB | 8GB | Excellent | Fast | General use |
| mistral | ~4GB | 8GB | Excellent | Fast | Reasoning |
| qwen2.5 | ~4.5GB | 8GB | Excellent | Fast | Multilingual |
| phi3 | ~2GB | 4GB | Good | Very Fast | Low-resource |
| llama3.1:8b | ~4.5GB | 8GB | Excellent | Medium | Quality |
| gemma2 | ~5GB | 8GB | Great | Fast | Instruction following |

## Advanced Configuration

### Custom Ollama Endpoint

If Ollama is running on a different host/port:

```python
wrapper = GLCSWrapper(
    provider='ollama',
    model='llama3.2',
    endpoint='http://192.168.1.100:11434'
)
```

### Multiple Models

Switch between models dynamically:

```python
# Start with llama3.2
wrapper = GLCSWrapper(provider='ollama', model='llama3.2')

# Switch to mistral for complex reasoning
wrapper.switch_provider('ollama', model='mistral')
```

### Model Parameters

Adjust generation parameters:

```python
result = wrapper.generate(
    "Explain quantum computing",
    temperature=0.8,  # More creative
    max_tokens=500    # Longer response
)
```

## Best Practices

1. **Start small**: Begin with `llama3.2` or `phi3`
2. **Monitor resources**: Watch RAM usage, especially with larger models
3. **Use appropriate timeout**: Increase for larger/complex prompts
4. **Model selection**: Use specialized models for specific tasks
5. **Keep models updated**: `ollama pull <model>` to get latest versions

## Performance Tips

### For Best Speed:
```python
wrapper = GLCSWrapper(
    provider='ollama',
    model='phi3',  # Fastest model
    temperature=0.3  # Less randomness = faster
)
```

### For Best Quality:
```python
wrapper = GLCSWrapper(
    provider='ollama',
    model='qwen2.5',  # High quality
    temperature=0.7,
    max_tokens=300  # More detailed responses
)
```

### For Privacy-Critical Applications:
```python
wrapper = GLCSWrapper(
    provider='ollama',
    model='mistral'
)

# Your data NEVER leaves your machine!
result = wrapper.generate("Sensitive information here...")
```

## FAQ

**Q: Do I need an API key for Ollama?**
A: No! Ollama runs completely locally, no API key needed.

**Q: Can I use Ollama offline?**
A: Yes, once models are downloaded, you can use them offline.

**Q: How much does Ollama cost?**
A: Ollama is completely free and open source.

**Q: Which model should I use?**
A: For most users, start with `llama3.2`. For better reasoning, try `mistral` or `qwen2.5`.

**Q: Can I use multiple models?**
A: Yes, you can switch models dynamically or use different models for different tasks.

**Q: Is my data private?**
A: Yes! All processing happens locally on your machine. No data is sent to any server.

**Q: How do I update models?**
A: Run `ollama pull <model>` to get the latest version.

## Resources

- **Ollama Website:** https://ollama.ai
- **Ollama GitHub:** https://github.com/ollama/ollama
- **Model Library:** https://ollama.ai/library
- **GLCS Documentation:** https://github.com/GireeshS22/Global-Logic-Context-Store

## Next Steps

1. ✅ Install Ollama
2. ✅ Pull a model: `ollama pull llama3.2`
3. ✅ Test with GLCS (see "Testing Your Setup" above)
4. ✅ Read the [Provider Guide](PROVIDER_GUIDE.md) for provider comparison
5. ✅ Explore different models and find what works best for you

Happy local LLM usage! 🚀
