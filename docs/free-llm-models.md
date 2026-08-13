# OpenRouter Free LLM Models — LCA-GPT Reference

> **Last updated:** 2026-08-13  
> **Account limits:** 50 req/day (free) → 1 000 req/day (after adding $10 credits)  
> **All limits are account-wide, shared across every `:free` model.**  
> Set `OPENROUTER_MODEL=<slug>` in `.env` to switch.

---

## ✅ Currently in Use

### `poolside/laguna-s-2.1:free`
| Property | Value |
|----------|-------|
| Context window | 262 144 tokens |
| Max output | 32 768 tokens |
| Parameters | 118B total / 8B active (MoE) |
| Reasoning | ❌ Non-reasoning |
| Tool calling | ✅ Yes |
| `response_format` | ❌ Not supported (use prompt-based JSON) |
| Latency (tested) | ~3–6 s chat · ~6.6 s PDF extraction |

**What it can do:**  
Coding-agent model from Poolside. Excels at agentic coding tasks, function calling, tool use, and long-context reasoning over code repositories. Scores 70.2% on Terminal-Bench 2.1 and 40.4% on DeepSWE — one of the strongest free coding models available.  
Open-weight under the OpenMDW-1.1 license.

**Best for in LCA-GPT:** PDF extraction (`analyzer.py`), RAG Q&A (`graph_rag.py`), general chat.  
**Caveats:** Does NOT support `response_format` kwarg — use prompt engineering for JSON output (confirmed working). Free tier may be time-limited per Poolside's promotional policy.

---

## 🧪 Previously Tested

### `liquid/lfm-2.5-2.6b:free`
| Property | Value |
|----------|-------|
| Context window | 128 000 tokens |
| Max output | varies |
| Parameters | 2.6B |
| Reasoning | ⚠️ MANDATORY (cannot be disabled) |
| Tool calling | ✅ Yes |
| `response_format` | ❌ Not supported |
| Latency (tested) | ~37 s chat · ~230 s PDF extraction |

**What it can do:**  
Liquid Foundation Model with mandatory built-in reasoning. Uses Liquid Neural Network architecture. Reasoning tokens are billed against `max_tokens` *before* any visible output is produced — set `max_tokens ≥ 4000` for extraction, `≥ 2000` for Q&A, or `content` returns `None`.

**Best for in LCA-GPT:** Acceptable for low-traffic scenarios where accuracy matters more than speed.  
**Caveats:** Very slow (~4 min extraction). Passing `reasoning: {enabled: false}` returns HTTP 400. Always guard `if not content` after every API call. **Not recommended for production.**

---

### `google/gemma-4-26b-a4b-it:free`
| Property | Value |
|----------|-------|
| Context window | 262 144 tokens |
| Max output | 8 192 tokens |
| Parameters | 26B (A4B active, MoE) |
| Reasoning | ❌ Non-reasoning |
| Tool calling | ✅ Yes |
| Latency (tested) | ~3–5 s (when available) |

**What it can do:**  
Google Gemma 4 multimodal instruction-tuned model. Supports text and image inputs. Fast non-reasoning responses. Strong general-purpose performance.

**Best for in LCA-GPT:** Would be suitable for extraction and Q&A if stable.  
**Caveats:** ❌ **Avoid.** Backed by Google AI Studio shared pool — persistent upstream 429 errors. All 5 retries (0 s, 2 s, 5 s, 10 s, 20 s backoff) fail. Not a transient issue; the free shared pool is chronically overloaded.

---

### `nvidia/nemotron-nano-12b-v2-vl:free`
| Property | Value |
|----------|-------|
| Context window | 128 000 tokens |
| Parameters | 12B |
| Reasoning | ❌ Non-reasoning |
| Tool calling | ✅ Yes |
| Modalities | Text + Vision (image input) |

**What it can do:**  
Compact vision-language model from NVIDIA. Accepts image inputs alongside text — useful for invoice/document images if PDF-to-image conversion is added.

**Caveats:** ⚠️ Reliability issues observed during testing (intermittent failures). Not confirmed stable enough for production extraction pipeline.

---

### `nvidia/nemotron-3-embed-1b:free`
| Property | Value |
|----------|-------|
| Endpoint | `/v1/embeddings` only |
| Dimensions | 4 096 |
| Context window | 8 192 tokens |

**What it can do:**  
Generates dense vector embeddings for semantic similarity search. Serves `/embeddings` endpoint — **not `/chat/completions`**.

**Best for in LCA-GPT:** Could replace the TF bag-of-words cosine similarity in `vector_store.py` with real semantic embeddings — would dramatically improve `find_similar_audits()` recall quality.  
**Caveats:** ❌ Cannot generate text. Calling `/chat/completions` returns HTTP 400. Use only for embedding, not generation.

---

## 🔍 Researched — Untested, Promising

### `nvidia/nemotron-3-ultra-550b-a55b:free`
| Property | Value |
|----------|-------|
| Context window | 1 000 000 tokens |
| Max output | 65 536 tokens |
| Parameters | 550B total / 55B active (MoE) |
| Reasoning | ✅ Optional (can enable/disable) |
| Tool calling | ✅ Yes |
| Architecture | Hybrid Transformer-Mamba MoE |

**What it can do:**  
NVIDIA's largest free model. Frontier-class reasoning and orchestration. The 1M context window can ingest entire codebases or very long document sets in one pass. Hybrid Mamba-Transformer architecture gives better long-sequence efficiency than pure Transformers.

**Best for in LCA-GPT:** Complex multi-step reasoning, large-batch document analysis, orchestrating multi-agent workflows.  
**Caveats:** Largest model on this list — likely higher latency than Laguna S. Reasoning is optional (not mandatory), so it behaves like a non-reasoning model by default. Worth benchmarking if Laguna S extraction quality is insufficient.

---

### `nvidia/nemotron-3-super-120b-a12b:free`
| Property | Value |
|----------|-------|
| Context window | 262 144 tokens |
| Max output | 262 144 tokens |
| Parameters | 120B total / 12B active (MoE) |
| Reasoning | ✅ Optional |
| Tool calling | ✅ Yes |
| Architecture | Hybrid Mamba-Transformer MoE |

**What it can do:**  
Mid-tier NVIDIA model optimised for agentic reasoning, coding, and tool use in multi-agent applications. Same Mamba-Transformer hybrid as Ultra but cheaper to run (12B active). Strong at structured code generation and complex tool-use chains.

**Best for in LCA-GPT:** Multi-step agentic tasks, function chaining, complex extraction with tool calling.  
**Caveats:** Provider-limited to 262K despite native support for more. Reasoning optional — default is non-reasoning mode.

---

### `poolside/laguna-xs-2.1:free`
| Property | Value |
|----------|-------|
| Context window | 256 000 tokens |
| Max output | 32 768 tokens |
| Reasoning | ✅ Optional (interleaved) |
| Tool calling | ✅ Yes (JSON schema) |
| Quantization | FP8 |

**What it can do:**  
Smaller sibling of the current `laguna-s-2.1`. Combines tool calling and interleaved reasoning in a compact FP8-quantized footprint. Released April 2026. Designed for fast, cost-efficient agentic coding workflows where latency matters.

**Best for in LCA-GPT:** Drop-in replacement for Laguna S if latency needs to drop further; useful for lightweight tool-calling sub-agents.  
**Caveats:** Smaller than Laguna S — may produce lower-quality extraction JSON on complex POs. Needs benchmarking before switching.

---

### `cohere/north-mini-code:free`
| Property | Value |
|----------|-------|
| Context window | 256 000 tokens |
| Max output | 64 000 tokens |
| Reasoning | ✅ Interleaved reasoning |
| Tool calling | ✅ Yes (JSON schema) |
| License | Apache 2.0 (open-weight) |

**What it can do:**  
Cohere's coding model with interleaved reasoning and tool use. 64K max output is the highest of any free model — excellent for tasks that require long structured outputs (e.g., large JSON extraction results). Apache 2.0 license means it can be self-hosted.

**Best for in LCA-GPT:** Long-form JSON extraction where output may exceed Laguna S's response size. Could be a fallback if Laguna S truncates large PO documents.  
**Caveats:** Reasoning is interleaved (not mandatory) — test whether it activates during JSON extraction and adds latency. Untested in this project.

---

### `nvidia/nemotron-3-nano-omni-30b-a3b:free`
| Property | Value |
|----------|-------|
| Context window | ~128 000 tokens |
| Parameters | 30B total / 3B active (MoE) |
| Reasoning | ✅ Optional |
| Tool calling | ✅ Yes |
| Modalities | Text + Image + Video + Audio |

**What it can do:**  
Multimodal perception and context sub-agent. Designed to act as a sensor layer in enterprise agent systems — ingests text, image, video, and audio in a single inference call. Useful if the pipeline needs to process invoice images or scanned PDFs directly without PyMuPDF.

**Best for in LCA-GPT:** Future multimodal ingestion pipeline — e.g., pass scanned purchase order images directly without PDF text extraction step.  
**Caveats:** 3B active parameters — likely weaker reasoning than larger models. Optimised for perception, not complex generation. Untested.

---

## ❌ Removed / Deprecated

| Model slug | Reason |
|------------|--------|
| `tencent/hy3:free` | ⚠️ Deprecated July 2026, being delisted |
| `poolside/laguna-m-2.1:free` | Delisted from OpenRouter ~August 2026 |
| `meta-llama/*:free` | Entire free Llama tier removed |
| `qwen/*:free` | Entire free Qwen tier removed (went paid) |

---

## Quick Comparison

| Slug | Context | Reasoning | Tools | Tested | Recommended for LCA-GPT |
|------|---------|-----------|-------|--------|--------------------------|
| `poolside/laguna-s-2.1:free` | 262K | ❌ None | ✅ | ✅ Yes | ⭐ **Current — extraction + Q&A** |
| `poolside/laguna-xs-2.1:free` | 256K | Optional | ✅ | ❌ No | Fast fallback / sub-agent |
| `cohere/north-mini-code:free` | 256K | Interleaved | ✅ | ❌ No | Long JSON extraction |
| `nvidia/nemotron-3-super-120b-a12b:free` | 262K | Optional | ✅ | ❌ No | Multi-agent orchestration |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | 1M | Optional | ✅ | ❌ No | Large-doc reasoning |
| `nvidia/nemotron-3-nano-omni-30b-a3b:free` | 128K | Optional | ✅ | ❌ No | Future multimodal ingestion |
| `nvidia/nemotron-3-embed-1b:free` | 8K | N/A | N/A | ✅ Yes | Embeddings only (vector_store) |
| `liquid/lfm-2.5-2.6b:free` | 128K | ⚠️ Mandatory | ✅ | ✅ Yes | ❌ Too slow |
| `google/gemma-4-26b-a4b-it:free` | 262K | ❌ None | ✅ | ✅ Yes | ❌ Upstream 429 |
| `nvidia/nemotron-nano-12b-v2-vl:free` | 128K | ❌ None | ✅ | ✅ Yes | ❌ Reliability issues |

---

## OpenRouter Rate Limit Notes

- Free account: **50 req/day** across ALL `:free` models combined
- Add $10 credits once → **1 000 req/day** permanently
- Limits reset at **00:00 UTC** daily
- Per-minute burst limit: ~20 req/min (`free-models-per-min`)
- Adding extra API keys does **not** bypass limits — they are per-account

---

# Other Providers (Non-OpenRouter)

> All providers below are OpenAI SDK-compatible (`base_url` swap only).  
> Change `base_url` + `api_key` in code; no other changes needed.

---

## 🚀 Groq — Fastest Free Tier

**Base URL:** `https://api.groq.com/openai/v1`  
**OpenAI SDK compatible:** ✅  
**Embedding endpoint:** ❌ No  
**Sign-up:** [console.groq.com](https://console.groq.com) — no credit card required

Groq runs on custom LPU (Language Processing Unit) chips, not GPUs. Output speed is **500–1 800 tokens/second** — an order of magnitude faster than GPU-based APIs. Best choice for fast extraction in LCA-GPT.

### Free Tier Limits
| Limit | Value |
|-------|-------|
| Requests/min | ~30 RPM |
| Requests/day | ~14 400 RPD |
| Token budget | Per-model TPM (e.g. ~12K TPM on Llama 3.3 70B) |
| Cost | $0 — no credit card |

### Key Models

| Model ID | Context | Speed | Notes |
|----------|---------|-------|-------|
| `llama-3.3-70b-versatile` | 128K | **394 TPS** | Best quality free model on Groq; strong JSON extraction |
| `llama-3.1-8b-instant` | 128K | **840 TPS** | Fastest; lighter quality — good for Q&A, not complex extraction |
| `qwen-3.6-27b` | 131K | **500 TPS** | Dense 27B, hybrid multimodal (text/image/video) |
| `gpt-oss-120b` | 128K | **500 TPS** | OpenAI open-weight MoE; strong reasoning + tool use |

**Best for LCA-GPT:** `llama-3.3-70b-versatile` — 394 TPS means a typical extraction completes in **< 2 s** vs 6 s on Laguna S. Drop-in replacement via `base_url`.

**Caveats:** No embedding endpoint. Per-model TPM cap can hit during burst extraction of many documents. Limits are per API key (creating multiple keys helps here, unlike OpenRouter).

---

## ⚡ Cerebras — Ultra-Fast, Low Daily Cap

**Base URL:** `https://api.cerebras.ai/v1`  
**OpenAI SDK compatible:** ✅  
**Embedding endpoint:** ❌ No  
**Sign-up:** [cloud.cerebras.ai](https://cloud.cerebras.ai) — no credit card required

Cerebras wafer-scale chip delivers the highest raw throughput of any free API. Llama 3.1 8B runs at **1 800 TPS**; Llama 3.3 70B at **450 TPS**. The catch is a low daily token cap.

### Free Tier Limits
| Limit | Value |
|-------|-------|
| Requests/min | **5 RPM** |
| Tokens/day | **1 000 000 TPD** (~24M tokens/day at paid) |
| Models | 2 models on free tier |
| Cost | $0 — no credit card |

### Key Models

| Model ID | Context | Speed | Notes |
|----------|---------|-------|-------|
| `llama-3.1-8b` | 128K | **1 800 TPS** | Fastest model on any free API |
| `llama-3.3-70b` | 128K | **450 TPS** | Best quality on Cerebras free tier |
| `glm-4.7` | ~128K | **1 000 TPS** | Best-in-class code generation per Cerebras |

**Best for LCA-GPT:** Burst extraction jobs — finish in milliseconds per call. 5 RPM cap means only 5 extractions/min, but each is near-instant.

**Caveats:** Only 2 models on free tier. 5 RPM is very restrictive for burst workloads. 1M TPD is generous for low-volume pipelines.

---

## 🌐 Google Gemini API (Direct) — High Daily Cap

**Base URL:** `https://generativelanguage.googleapis.com/v1beta/openai/` (OpenAI-compat)  
**OpenAI SDK compatible:** ✅ (via OpenAI-compat endpoint)  
**Embedding endpoint:** ✅ Yes (`text-embedding-004`, `gemini-embedding-exp-03-07`)  
**Sign-up:** [aistudio.google.com](https://aistudio.google.com) — free, no credit card

> ⚠️ **Important distinction:** This is the **direct Gemini API** — NOT via OpenRouter.  
> The OpenRouter `google/gemma-4-26b-it:free` route goes through Google AI Studio's shared pool and is chronically overloaded. The direct API below is separate, more reliable, and has higher limits.

### Free Tier Limits (per Google Cloud project)
| Model | RPM | RPD | TPM |
|-------|-----|-----|-----|
| Gemini 2.5 Flash-Lite | 15 | **1 000** | 250K |
| Gemini 2.5 Flash | 10 | **250** | 250K |
| Gemini 2.5 Pro | 5 | 100 | 250K |

### Key Models

| Model ID | Context | Reasoning | Notes |
|----------|---------|-----------|-------|
| `gemini-2.5-flash-lite` | 1M | Optional | 1 000 req/day free; fastest Gemini; best value |
| `gemini-2.5-flash` | 1M | Optional (thinking levels) | 250 req/day; strong extraction + structured output |
| `gemini-2.5-pro` | 1M | Optional | 100 req/day; highest quality |

### Embedding Models (free)
| Model ID | Dimensions | Notes |
|----------|-----------|-------|
| `text-embedding-004` | 768 | Stable, fast, good for RAG retrieval |
| `gemini-embedding-exp-03-07` | 3 072 | Experimental; highest quality |

**Best for LCA-GPT:** `gemini-2.5-flash-lite` for extraction (1 000 req/day free, 1M context) + `text-embedding-004` to replace `vector_store.py` TF bag-of-words with real semantic embeddings — both from the same API key.

**Caveats:** 1M context window but 15 RPM max on Flash-Lite. Reasoning tokens add latency when thinking is enabled — disable with `thinking: {budget_tokens: 0}` for extraction tasks. Rate limits are per Google Cloud **project**, not per API key — multiple keys on the same project share the same quota.

---

## 🤗 Hugging Face Serverless Inference — 150K+ Models

**Base URL:** `https://router.huggingface.co` (via inference-providers)  
**OpenAI SDK compatible:** ✅ (for supported models)  
**Embedding endpoint:** ✅ Yes — hundreds of free embedding models  
**Sign-up:** [huggingface.co](https://huggingface.co) — free account, no credit card

### Free Tier Limits
| Limit | Value |
|-------|-------|
| Requests | ~30 req / 30 s (~60 RPM) |
| Models | 150 000+ (not all support serverless) |
| Cost | $0 on free account |

### Key LLM Models (serverless)

| Model ID | Context | Notes |
|----------|---------|-------|
| `meta-llama/Llama-3.3-70B-Instruct` | 128K | Best free quality; rate-limited |
| `Qwen/Qwen2.5-72B-Instruct` | 128K | Strong multilingual + JSON output |
| `mistralai/Mistral-7B-Instruct-v0.3` | 32K | Lightweight, fast, reliable |

### Key Embedding Models (serverless — free)

| Model ID | Dimensions | Notes |
|----------|-----------|-------|
| `BAAI/bge-large-en-v1.5` | 1 024 | Top-performing open embedding model |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Ultra-fast, compact; great for prototyping |
| `nomic-ai/nomic-embed-text-v1.5` | 768 | Long context (8K), Apache 2.0 |
| `thenlper/gte-large` | 1 024 | Strong semantic search, multilingual |

**Best for LCA-GPT:** Embedding models — use `BAAI/bge-large-en-v1.5` or `nomic-ai/nomic-embed-text-v1.5` to upgrade `vector_store.py` from TF bag-of-words to real semantic search. Free, no daily cap issues for embeddings.

**Caveats:** LLM inference is unreliable at free tier (cold starts, queue waits). Better for embeddings than generation. PRO account ($9/month) raises to 500 RPM.

---

## Cross-Provider Quick Comparison

| Provider | Best Model (free) | Speed | RPM | RPD | Embeddings | LCA-GPT Use |
|----------|------------------|-------|-----|-----|-----------|-------------|
| **OpenRouter** | `poolside/laguna-s-2.1:free` | ~150 TPS | ~20 | 50 (1K w/$10) | ✅ `nemotron-3-embed-1b` | ⭐ Current |
| **Groq** | `llama-3.3-70b-versatile` | **394 TPS** | 30 | 14 400 | ❌ | ⭐⭐ Best for extraction speed |
| **Cerebras** | `llama-3.3-70b` | **450 TPS** | 5 | ~300* | ❌ | Fast but low RPM |
| **Gemini Direct** | `gemini-2.5-flash-lite` | ~200 TPS | 15 | **1 000** | ✅ `text-embedding-004` | ⭐⭐ Best all-in-one |
| **Hugging Face** | `bge-large-en-v1.5` (embed) | fast | ~60 | unlimited | ✅ 150K models | ⭐⭐ Best for embeddings |

*Cerebras 1M TPD ÷ ~3K tokens/extraction ≈ 333 extractions/day

---

## Recommendation for LCA-GPT

**For immediate speed boost (drop-in, no code refactor):**  
→ Switch to **Groq** `llama-3.3-70b-versatile`. Change `base_url` to `https://api.groq.com/openai/v1` and get a free key from [console.groq.com](https://console.groq.com). Extraction will drop from ~6 s to **~1–2 s**.

**For highest daily quota + embeddings (one API key for everything):**  
→ Use **Google Gemini Direct** — `gemini-2.5-flash-lite` for generation (1 000 req/day) + `text-embedding-004` for `vector_store.py` semantic search upgrade.

**For real semantic search (best quality, free):**  
→ Add **Hugging Face** `BAAI/bge-large-en-v1.5` as the embedding model in `vector_store.py`. No daily cap on embeddings.

---

## Sources

- [Free AI Models on OpenRouter](https://openrouter.ai/collections/free-models)
- [OpenRouter FREE Models · GitHub Gist](https://gist.github.com/rlnorthcutt/e6f392cd1ffb1339cc42dfb024c3cf7f)
- [All 14 Live Free Models — teamday.ai](https://www.teamday.ai/blog/best-free-ai-models-openrouter-2026)
- [North Mini Code (free)](https://openrouter.ai/cohere/north-mini-code:free)
- [Laguna XS 2.1 (free)](https://openrouter.ai/poolside/laguna-xs-2.1:free)
- [OpenRouter Free Router Docs](https://openrouter.ai/docs/guides/routing/routers/free-router)
- [13 Free LLM Options Ranked — OpenRouter Blog](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/)
- [Groq Free Tier 2026 — pricepertoken.com](https://pricepertoken.com/endpoints/groq/free)
- [Groq API Free Tier Limits — grizzlypeaksoftware.com](https://www.grizzlypeaksoftware.com/articles/p/groq-api-free-tier-limits-in-2026-what-you-actually-get-uwysd6mb)
- [Groq Supported Models](https://console.groq.com/docs/models)
- [Cerebras Rate Limits](https://inference-docs.cerebras.ai/support/rate-limits)
- [Cerebras Models Overview](https://inference-docs.cerebras.ai/models/overview)
- [Cerebras Pricing 2026 — morphllm.com](https://www.morphllm.com/cerebras-pricing)
- [Gemini API Free Tier Guide — aifreeapi.com](https://www.aifreeapi.com/en/posts/gemini-api-free-tier-complete-guide)
- [Gemini API Rate Limits — ai.google.dev](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Hugging Face Serverless Inference API](https://huggingface.co/docs/api-inference/en/index)
- [HuggingFace Rate Limits — Hub Docs](https://huggingface.co/docs/hub/rate-limits)
- [Awesome Free LLM APIs — GitHub](https://github.com/amardeeplakshkar/awesome-free-llm-apis)
