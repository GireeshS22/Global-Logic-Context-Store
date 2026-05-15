# GLCS Provider Guide

Complete guide to choosing and using LLM providers with GLCS.

## Quick Comparison

| Provider | Cost (per 1K parses) | Speed | Quality | Privacy | Setup | Recommended For |
|---|---|---|---|---|---|---|
| **Ollama** | **FREE** | Fast | Good | Local | Medium | Development, Privacy |
| **OpenAI** | ~$0.06 | Very Fast | Excellent | Cloud | Easy | Production |
| **Gemini** | ~$0.04 | Very Fast | Great | Cloud | Easy | Budget-conscious |
| **Anthropic** | ~$0.05 | Fast | Excellent | Cloud | Easy | Quality focus |
| **Together AI** | ~$0.03 | Fast | Good | Cloud | Easy | Open-source models |
| **xAI (Grok)** | ~$0.04 | Fast | Excellent | Cloud | Easy | Reasoning tasks |
| **Groq** | ~$0.07 | **Ultra Fast** | Good | Cloud | Easy | Speed-critical |

---

## Provider Details

### 1. Ollama (Local Models)

Run LLMs **completely locally** — no API keys, no costs, 100% private.

**Pros:** Free, private, offline-capable, no API key needed  
**Cons:** Requires local RAM/GPU, initial model downloads (2–8 GB)

```python
from glcs import GLCSWrapper
wrapper = GLCSWrapper(provider='ollama')
```

**Recommended models:**
- `llama3.2` — best all-around (2 GB)
- `mistral` — best for reasoning (4 GB)
- `qwen2.5` — best for multilingual (4.5 GB)
- `phi3` — best for low-resource machines (2 GB)

See [Ollama Setup Guide](OLLAMA_SETUP.md) for installation.

---

### 2. OpenAI (GPT-4o, GPT-4o-mini)

Industry-standard models. Best reliability and ecosystem support.

```bash
export OPENAI_API_KEY=sk-...
```

```python
wrapper = GLCSWrapper(provider='openai')               # gpt-4o-mini (default)
wrapper = GLCSWrapper(provider='openai', model='gpt-4o')  # best quality
```

**Pricing:**
- `gpt-4o-mini`: ~$0.06 per 1K parses
- `gpt-4o`: ~$1.00 per 1K parses

**Get API key:** https://platform.openai.com/api-keys

---

### 3. Google Gemini (2.5 Flash, 2.5 Pro)

Best price/performance ratio. Largest context window.

```bash
export GOOGLE_API_KEY=AIza...
```

```python
wrapper = GLCSWrapper(provider='gemini')                           # gemini-2.5-flash (default)
wrapper = GLCSWrapper(provider='gemini', model='gemini-2.5-pro')  # best quality
```

**Pricing:**
- `gemini-2.5-flash`: ~$0.04 per 1K parses
- `gemini-2.5-pro`: ~$0.50 per 1K parses

**Get API key:** https://aistudio.google.com/app/apikey

> **Note:** GLCS uses the `google-genai` SDK. The older `google-generativeai` package is deprecated. If you have a new API key, use `gemini-2.5-flash` or newer — `gemini-1.5-flash` and `gemini-2.0-flash` are restricted for newer accounts.

---

### 4. Anthropic Claude (Haiku, Sonnet)

Known for safety, alignment, and strong reasoning.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

```python
wrapper = GLCSWrapper(provider='anthropic')                                      # claude-haiku-4-5 (default)
wrapper = GLCSWrapper(provider='anthropic', model='claude-sonnet-4-6')           # best quality
```

**Pricing:**
- `claude-haiku-4-5-20251001`: ~$0.05 per 1K parses
- `claude-sonnet-4-6`: ~$1.50 per 1K parses

**Get API key:** https://console.anthropic.com/

---

### 5. Together AI (Open-source models)

Wide variety of open-source models via a simple OpenAI-compatible API.

```bash
export TOGETHER_API_KEY=...
```

```python
wrapper = GLCSWrapper(provider='together')  # Llama-3.3-70B-Instruct-Turbo (default)
wrapper = GLCSWrapper(provider='together', model='Qwen/Qwen2.5-72B-Instruct-Turbo')
```

**Pricing:** ~$0.03–$0.10 per 1K parses depending on model  
**Get API key:** https://api.together.ai/settings/api-keys

---

### 6. xAI — Grok

Grok models from xAI. OpenAI-compatible API.

```bash
export XAI_API_KEY=...
```

```python
wrapper = GLCSWrapper(provider='xai')                           # grok-3-mini (default)
wrapper = GLCSWrapper(provider='xai', model='grok-3')           # best quality
wrapper = GLCSWrapper(provider='grok')                          # alias for xai
```

**Pricing:** ~$0.04–$0.30 per 1K parses  
**Get API key:** https://console.x.ai/

---

### 7. Groq (Ultra-fast inference)

Fastest cloud inference available, using open-source models.

```bash
export GROQ_API_KEY=gsk_...
```

```python
wrapper = GLCSWrapper(provider='groq')                                     # mixtral-8x7b (default)
wrapper = GLCSWrapper(provider='groq', model='llama-3.1-70b-versatile')   # best quality
```

**Pricing:**
- `mixtral-8x7b-32768`: ~$0.27 per 1M tokens
- `llama-3.1-8b-instant`: ~$0.07 per 1K parses (cheapest Groq option)

**Get API key:** https://console.groq.com/keys

---

## Decision Tree

**Use Ollama when:** free usage, privacy-critical, offline, or developing/testing  
**Use OpenAI when:** production reliability is critical, largest ecosystem needed  
**Use Gemini when:** budget-conscious cloud, huge context window (1M tokens)  
**Use Anthropic when:** safety-critical, nuanced reasoning, quality over cost  
**Use Together AI when:** prefer open-source models, want model variety  
**Use xAI when:** strong reasoning tasks, want to try Grok models  
**Use Groq when:** speed is the top priority, real-time applications  

---

## Cost Comparison (1 Million Parses)

| Provider | Model | Cost |
|---|---|---|
| Ollama | any | **$0** (FREE) |
| Together AI | Llama-3.3-70B-Turbo | ~$30 |
| Gemini | 2.5 Flash | ~$40 |
| OpenAI | gpt-4o-mini | ~$60 |
| Anthropic | claude-haiku-4-5 | ~$50 |
| Groq | llama-3.1-8b-instant | ~$70 |
| xAI | grok-3-mini | ~$40 |
| OpenAI | gpt-4o | ~$1,000 |
| Anthropic | claude-sonnet-4-6 | ~$1,500 |

---

## Switching Providers

```python
from glcs import GLCSWrapper

wrapper = GLCSWrapper(provider='openai')
result1 = wrapper.generate("Test prompt")

# Switch provider dynamically
wrapper.switch_provider('ollama')
result2 = wrapper.generate("Private prompt")
```

## Multi-Provider Strategy

```python
# Development: free local
dev = GLCSWrapper(provider='ollama')

# Production: reliable cloud
prod = GLCSWrapper(provider='openai', model='gpt-4o-mini')

# Speed-critical: ultra-fast
fast = GLCSWrapper(provider='groq', model='mixtral-8x7b-32768')

# Privacy-critical: local only
private = GLCSWrapper(provider='ollama', model='mistral')
```

---

## Environment Variables

```bash
GLCS_DEFAULT_PROVIDER=openai

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001

GOOGLE_API_KEY=AIza...
GEMINI_MODEL=gemini-2.5-flash

GROQ_API_KEY=gsk_...
GROQ_MODEL=mixtral-8x7b-32768

TOGETHER_API_KEY=...
TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo

XAI_API_KEY=...
XAI_MODEL=grok-3-mini

# Local
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b
```

---

## Smoke Testing All Providers

Verify all configured providers work end-to-end before deploying:

```bash
poetry run python scripts/smoke_test_providers.py
```

This tests each provider with raw generation, logical parsing, and consistency scoring — showing the exact messages sent and responses received.

---

## FAQ

**Which provider should I use for production?**  
OpenAI `gpt-4o-mini` for reliability; Gemini `gemini-2.5-flash` for lowest cost.

**Which is completely free?**  
Ollama (runs locally). All cloud providers charge per token.

**Can I use multiple providers in one app?**  
Yes — switch providers dynamically or use different `GLCSWrapper` instances.

**Which is fastest?**  
Groq for cloud. Ollama can match cloud speeds on good hardware.

**Which is most private?**  
Only Ollama — data never leaves your machine. All cloud providers transmit data.

**Do Together AI and xAI need a special SDK?**  
No — they use the OpenAI-compatible API, so the `openai` Python package handles both.
