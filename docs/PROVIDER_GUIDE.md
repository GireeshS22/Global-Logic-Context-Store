# GLCS Provider Guide

Complete guide to choosing and using LLM providers with GLCS.

## Quick Comparison

| Provider | Cost (per 1K parses) | Speed | Quality | Privacy | Setup Difficulty | Recommended For |
|----------|---------------------|-------|---------|---------|------------------|-----------------|
| **Ollama** (llama3.2) | **FREE** | Fast | Good | 🔒 100% Local | Medium | Development, Privacy |
| **OpenAI** (gpt-4o-mini) | $0.06 | Very Fast | Excellent | ☁️ Cloud | Easy | Production |
| **Gemini** (1.5 Flash) | $0.04 | Very Fast | Great | ☁️ Cloud | Easy | Budget-conscious |
| **Anthropic** (Claude 3 Haiku) | $0.08 | Fast | Excellent | ☁️ Cloud | Easy | Quality focus |
| **Groq** (Mixtral) | $0.27 | **Ultra Fast** | Good | ☁️ Cloud | Easy | Speed critical |

## Provider Details

### 1. Ollama (Local Models)

#### Overview
Run LLMs **completely locally** on your machine. No API keys, no costs, 100% private.

#### Pros
- ✅ **FREE** - No costs at all
- ✅ **100% Private** - Data never leaves your machine
- ✅ **Offline** - Works without internet
- ✅ **No API keys** - No account needed
- ✅ **Good quality** - Competitive with cloud models
- ✅ **Multiple models** - Choose from many open-source models

#### Cons
- ❌ Requires local resources (RAM, CPU/GPU)
- ❌ Initial setup required
- ❌ Slower than cloud on low-end hardware
- ❌ Model downloads can be large (2-8GB)

#### Setup
See [Ollama Setup Guide](OLLAMA_SETUP.md) for detailed instructions.

```python
from glcs import GLCSWrapper

wrapper = GLCSWrapper(provider='ollama')
```

#### Best Models
- `llama3.2` - Best all-around (2GB, excellent quality)
- `mistral` - Best for reasoning (4GB, excellent)
- `qwen2.5` - Best for multilingual (4.5GB, excellent)
- `phi3` - Best for low-resource (2GB, good quality)

#### When to Use
- 🎯 Development and testing
- 🎯 Privacy-critical applications
- 🎯 Offline environments
- 🎯 Budget constraints (FREE!)
- 🎯 Learning and experimentation

---

### 2. OpenAI (GPT-4o, GPT-4o-mini)

#### Overview
Industry-leading models from OpenAI. Best quality and performance.

#### Pros
- ✅ **Excellent quality** - State-of-the-art performance
- ✅ **Very fast** - Optimized infrastructure
- ✅ **Easy setup** - Just need API key
- ✅ **Reliable** - High uptime
- ✅ **Good documentation** - Well supported

#### Cons
- ❌ Costs money (though GPT-4o-mini is cheap)
- ❌ Data sent to cloud
- ❌ Requires API key
- ❌ Rate limits apply

#### Setup
```bash
# Get API key from: https://platform.openai.com/api-keys
export OPENAI_API_KEY=sk-...
```

```python
from glcs import GLCSWrapper

# Use gpt-4o-mini (recommended - cheapest)
wrapper = GLCSWrapper(provider='openai')

# Or use gpt-4o for best quality
wrapper = GLCSWrapper(provider='openai', model='gpt-4o')
```

#### Pricing
- **gpt-4o-mini**: $0.15/1M input + $0.60/1M output ≈ $0.06 per 1000 parses
- **gpt-4o**: $2.50/1M input + $10/1M output ≈ $1.00 per 1000 parses
- **gpt-3.5-turbo**: $0.50/1M input + $1.50/1M output ≈ $0.15 per 1000 parses

#### When to Use
- 🎯 **Production applications** (best reliability)
- 🎯 **Highest quality needed**
- 🎯 **Budget allows** (gpt-4o-mini is very affordable)
- 🎯 **Existing OpenAI integration**

---

### 3. Google Gemini (1.5 Pro, 1.5 Flash)

#### Overview
Google's latest models. Best price/performance ratio.

#### Pros
- ✅ **Cheapest cloud option** - Great value
- ✅ **Very fast** - Optimized infrastructure
- ✅ **Great quality** - Competitive with GPT-4
- ✅ **Huge context window** - 1M tokens!
- ✅ **Easy setup** - Simple API key

#### Cons
- ❌ Newer than competitors
- ❌ Data sent to cloud
- ❌ Requires API key
- ❌ Rate limits apply

#### Setup
```bash
# Get API key from: https://makersuite.google.com/app/apikey
export GOOGLE_API_KEY=AI...
```

```python
from glcs import GLCSWrapper

# Use Gemini 1.5 Flash (recommended - fastest & cheapest)
wrapper = GLCSWrapper(provider='gemini')

# Or use Gemini 1.5 Pro for best quality
wrapper = GLCSWrapper(provider='gemini', model='gemini-1.5-pro')
```

#### Pricing
- **Gemini 1.5 Flash**: $0.075/1M input + $0.30/1M output ≈ $0.04 per 1000 parses
- **Gemini 1.5 Pro**: $1.25/1M input + $5.00/1M output ≈ $0.50 per 1000 parses

#### When to Use
- 🎯 **Budget-conscious** (cheapest cloud option)
- 🎯 **Need speed AND quality**
- 🎯 **Large context needed** (1M tokens!)
- 🎯 **Google Cloud ecosystem**

---

### 4. Anthropic Claude (Claude 3.5, Claude 3)

#### Overview
Anthropic's Claude models. Known for helpfulness and safety.

#### Pros
- ✅ **Excellent quality** - Competitive with GPT-4
- ✅ **Very safe** - Strong safety guardrails
- ✅ **Good at reasoning** - Strong logical capabilities
- ✅ **Large context** - 200K tokens
- ✅ **Easy setup** - Simple API key

#### Cons
- ❌ Slightly more expensive than alternatives
- ❌ Data sent to cloud
- ❌ Requires API key
- ❌ Rate limits apply

#### Setup
```bash
# Get API key from: https://console.anthropic.com/
export ANTHROPIC_API_KEY=sk-ant-...
```

```python
from glcs import GLCSWrapper

# Use Claude 3 Haiku (recommended - fast & cheap)
wrapper = GLCSWrapper(provider='anthropic')

# Or use Claude 3.5 Sonnet for best quality
wrapper = GLCSWrapper(provider='anthropic', model='claude-3-5-sonnet-20241022')
```

#### Pricing
- **Claude 3 Haiku**: $0.25/1M input + $1.25/1M output ≈ $0.08 per 1000 parses
- **Claude 3.5 Sonnet**: $3.00/1M input + $15/1M output ≈ $1.50 per 1000 parses
- **Claude 3 Opus**: $15/1M input + $75/1M output ≈ $7.50 per 1000 parses

#### When to Use
- 🎯 **Safety-critical applications**
- 🎯 **Complex reasoning tasks**
- 🎯 **Prefer Anthropic's approach**
- 🎯 **Quality is top priority**

---

### 5. Groq (Mixtral, Llama)

#### Overview
Ultra-fast inference platform for open-source models.

#### Pros
- ✅ **Ultra fast** - Fastest inference available
- ✅ **Good quality** - Using proven open models
- ✅ **Easy setup** - Simple API key
- ✅ **Generous free tier** - Good for testing

#### Cons
- ❌ More expensive for high volume
- ❌ Limited model selection
- ❌ Data sent to cloud
- ❌ Newer service (less track record)

#### Setup
```bash
# Get API key from: https://console.groq.com/keys
export GROQ_API_KEY=gsk_...
```

```python
from glcs import GLCSWrapper

# Use Mixtral (recommended - balanced)
wrapper = GLCSWrapper(provider='groq')

# Or use Llama 3.1 for best quality
wrapper = GLCSWrapper(provider='groq', model='llama-3.1-70b-versatile')
```

#### Pricing
- **Mixtral 8x7B**: $0.27/1M tokens ≈ $0.27 per 1000 parses
- **Llama 3.1 70B**: $0.59/1M input + $0.79/1M output ≈ $0.70 per 1000 parses
- **Llama 3.1 8B**: $0.05/1M input + $0.08/1M output ≈ $0.07 per 1000 parses

#### When to Use
- 🎯 **Speed is critical** (fastest available)
- 🎯 **Real-time applications**
- 🎯 **Open-source model preference**
- 🎯 **Testing with generous free tier**

---

## Decision Tree

### Choose Ollama if:
- You want FREE usage
- Privacy is critical
- You have decent hardware (8GB RAM minimum)
- You're developing/testing
- You need offline capability

### Choose OpenAI if:
- You need best quality
- Reliability is critical
- Budget allows ($0.06+ per 1K with gpt-4o-mini)
- You're deploying to production
- You want the standard

### Choose Gemini if:
- You want best price/performance
- You need huge context (1M tokens)
- Speed is important
- You're in Google Cloud ecosystem
- Budget is tight but need quality

### Choose Claude if:
- Safety/alignment is critical
- You need strong reasoning
- You prefer Anthropic's approach
- Quality is more important than cost

### Choose Groq if:
- Speed is THE priority
- You're building real-time apps
- You like open-source models
- You want generous free tier for testing

---

## Cost Comparison (1 Million Parses)

| Provider | Model | Cost |
|----------|-------|------|
| Ollama | llama3.2 | **$0** (FREE) |
| Gemini | 1.5 Flash | **$40** (Cheapest cloud) |
| OpenAI | gpt-4o-mini | $60 |
| Anthropic | Claude 3 Haiku | $80 |
| Groq | Mixtral | $270 |
| OpenAI | gpt-4o | $1,000 |
| Anthropic | Claude 3.5 Sonnet | $1,500 |

---

## Switching Providers

You can easily switch providers:

```python
from glcs import GLCSWrapper

# Start with OpenAI
wrapper = GLCSWrapper(provider='openai')
result1 = wrapper.generate("Test prompt")

# Switch to Ollama for privacy
wrapper.switch_provider('ollama')
result2 = wrapper.generate("Private prompt")

# Switch to Gemini for cost savings
wrapper.switch_provider('gemini')
result3 = wrapper.generate("Another prompt")
```

---

## Multi-Provider Strategy

Use different providers for different purposes:

```python
# Development: Use free Ollama
dev_wrapper = GLCSWrapper(provider='ollama')

# Production: Use reliable OpenAI
prod_wrapper = GLCSWrapper(provider='openai', model='gpt-4o-mini')

# Privacy-critical: Use local Ollama
private_wrapper = GLCSWrapper(provider='ollama', model='mistral')

# Speed-critical: Use Groq
fast_wrapper = GLCSWrapper(provider='groq', model='mixtral-8x7b-32768')
```

---

## Recommendations by Use Case

### For Startups/Small Projects
**Recommended:** Gemini 1.5 Flash
- Cheapest cloud option ($0.04 per 1K)
- Great quality
- Easy to scale

**Alternative:** Ollama (FREE, but requires setup)

### For Enterprise Production
**Recommended:** OpenAI GPT-4o-mini
- Best reliability
- Excellent quality
- Industry standard
- Good price ($0.06 per 1K)

**Alternative:** Claude 3 Haiku (more safety features)

### For Privacy-Critical Applications
**Recommended:** Ollama (mistral or qwen2.5)
- 100% local
- No data leaves your machine
- FREE

**Alternative:** None - only Ollama provides true privacy

### For Development/Testing
**Recommended:** Ollama (llama3.2)
- FREE
- Fast enough
- Good quality
- Easy to experiment

**Alternative:** Groq (generous free tier)

### For Real-Time Applications
**Recommended:** Groq (Mixtral)
- Ultra-fast inference
- Low latency
- Reliable

**Alternative:** Gemini 1.5 Flash (very fast, cheaper)

---

## Configuration Examples

### Environment Variables (.env)
```bash
# Default provider
GLCS_DEFAULT_PROVIDER=openai

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
GROQ_API_KEY=gsk_...

# Model overrides (optional)
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-3-haiku-20240307
GEMINI_MODEL=gemini-1.5-flash
GROQ_MODEL=mixtral-8x7b-32768
OLLAMA_MODEL=llama3.2
```

### Config File (config/glcs_config.yaml)
```yaml
default_provider: openai

providers:
  openai:
    model: gpt-4o-mini
    temperature: 0.7

  gemini:
    model: gemini-1.5-flash
    temperature: 0.7

  ollama:
    model: llama3.2
    temperature: 0.7
```

---

## Getting API Keys

### OpenAI
1. Visit: https://platform.openai.com/api-keys
2. Sign up/log in
3. Create new API key
4. Copy and save securely

### Anthropic
1. Visit: https://console.anthropic.com/
2. Sign up/log in
3. Go to API Keys section
4. Create new key
5. Copy and save securely

### Google Gemini
1. Visit: https://makersuite.google.com/app/apikey
2. Sign up/log in with Google
3. Create API key
4. Copy and save securely

### Groq
1. Visit: https://console.groq.com/keys
2. Sign up/log in
3. Create API key
4. Copy and save securely

### Ollama
No API key needed! Just install: https://ollama.ai

---

## FAQ

**Q: Which provider should I use for production?**
A: OpenAI gpt-4o-mini offers the best reliability and quality for production use.

**Q: Which is the cheapest option?**
A: Ollama is completely FREE. For cloud options, Gemini 1.5 Flash is cheapest at $0.04 per 1K.

**Q: Can I use multiple providers?**
A: Yes! You can switch providers dynamically or use different providers for different tasks.

**Q: Which is fastest?**
A: Groq is the fastest cloud option. Ollama can be very fast on good hardware.

**Q: Which is most private?**
A: Only Ollama is 100% private (runs locally). All others send data to the cloud.

**Q: Do I need all API keys?**
A: No! Just get keys for the providers you want to use.

**Q: Can I switch providers without changing code?**
A: Yes! Use environment variables or config files to switch providers.

---

## Next Steps

1. ✅ Choose a provider based on your needs
2. ✅ Get API key (or install Ollama)
3. ✅ Configure GLCS (see examples above)
4. ✅ Test with simple prompts
5. ✅ Deploy to your application

For detailed setup instructions:
- **Ollama:** See [Ollama Setup Guide](OLLAMA_SETUP.md)
- **Others:** Just set the API key in `.env`

Happy prompting! 🚀
