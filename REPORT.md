# Technical Report — BusinessPilot AI: Offline Business Copilot

**Team:** DroneBug Technologies
**Domain:** corporate_enterprise
**Model:** tiny-aya-earth-Q4_K_M (Cohere Labs, 3.35B)
**Languages:** English, Hausa

---

## Problem

African SMEs and entrepreneurs face three compounding challenges: (1) unreliable or expensive internet connectivity making cloud SaaS tools impractical, (2) limited access to AI-powered business intelligence that requires cloud subscriptions, and (3) the administrative burden of task scheduling, financial tracking, data analysis, and document management on resource-constrained laptops. BusinessPilot AI solves this as a complete offline business assistant that runs entirely on an 8 GB RAM laptop with no GPU, no internet, and no cloud dependency — with full bilingual English/Hausa support.

Target users include micro-entrepreneurs, SME owners, accountants, and operations managers across Africa who need AI-enhanced scheduling, financial modeling, CSV data analysis, document Q&A, and bilingual chat — all running locally on a Lenovo T450-class machine.

---

## Design Decisions

- **Base model:** tiny-aya-earth (Cohere2 architecture, 3.35B, GGUF Q4_K_M). Chosen for its strong multilingual ability (English + Hausa), small 3.35B footprint, and instruction-following quality for structured business tasks.
- **Quantization:** Q4_K_M provides the best quality-to-RAM tradeoff for a 3.35B model on 8 GB RAM. Q8_0 (3.57 GB) would consume too much of the memory budget alongside the browser and OS.
- **Runtime:** llama-server.exe (b9895, Windows CPU build) — the only supported runtime per ADTC rules. No GPU required.
- **Frontend architecture:** Pure client-side single HTML file (`static/index.html`). No Python backend, no Streamlit, no Gradio. The frontend talks directly to llama-server's OpenAI-compatible API on `127.0.0.1:8083` via `fetch()`. CORS is enabled via `--ui-mcp-proxy`.
- **Charts:** Chart.js 4.4.7 (206 KB, bundled in `static/libs/`). Interactive bar, line, pie, and scatter plots — all rendered client-side with no server dependency.
- **CSV parsing:** PapaParse 5.4.1 — client-side CSV parsing with automatic type detection.
- **Markdown rendering:** marked.js 12.0.2 — renders AI responses as formatted Markdown.
- **Persistence:** Browser localStorage persists tasks, chat history, and knowledge base chunks across sessions. No external database needed.
- **Notifications:** Browser Notification API fires native Windows toasts when tasks are added, edited, deleted, or when AI analysis completes. No Python, no polling loops.
- **Bilingual support:** The system prompt tells the model to reply in whatever language the user writes in (English or Hausa). No separate language detection model needed.
- **Knowledge base:** Users upload `.md` or `.txt` files. Content is split into chunks on blank lines, stored in localStorage. When the user queries or chats, relevant chunks are matched by keyword scoring and injected as context into the AI prompt.
- **Alternatives rejected:** DeepSeek-R1-Distill-Qwen-7B was considered but at 7B Q4 it would leave insufficient headroom in 8 GB RAM. A Python/Streamlit backend was used in earlier iterations but was eliminated to reduce memory overhead and startup time.

---

## Constraints

- **Hardware:** Lenovo T450, 8 GB RAM, Intel Core i5-5300U (2 core/4 thread), integrated Intel HD Graphics 5500. No GPU acceleration.
- **Memory budget:** ~2.1 GB for llama-server + tiny-aya-earth Q4_K_M, ~150 MB for browser, ~50 MB for Python HTTP server. Total ~2.3 GB peak — within 8 GB.
- **Connectivity:** Fully offline during inference. Model weights downloaded once via `download_model.sh`; all subsequent operations use the local llama-server API on `127.0.0.1:8083`.
- **Power:** Q4_K_M quantization reduces memory bandwidth and CPU load for battery-conscious laptop operation.
- **No cloud services:** Zero outbound network requests during inference. All libraries bundled in `static/libs/`.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (localhost:8081)               │
│  ┌──────────────────────────────────────────────────┐   │
│  │              index.html (single page)             │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │   │
│  │  │ Home │ │Tasks │ │Data  │ │ KB   │ │Finance│  │   │
│  │  │Health│ │      │ │Chart │ │+Chat │ │CFO    │  │   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘  │   │
│  │       ↕ fetch() to http://127.0.0.1:8083         │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│        llama-server.exe (native C++, port 8083)          │
│  -m model/tiny-aya-earth-q4_k_m.gguf --ui-mcp-proxy     │
│  -c 2048 -t 4 -b 256 -ub 128 -np 1 --mmap               │
└─────────────────────────────────────────────────────────┘
```

---

## Benchmarks

Measured via llama-server (b9895) on Lenovo T450 (i5-5300U, 8 GB DDR3, Windows 10, CPU-only, 4 threads):

| Metric | Value |
|---|---|
| Machine | Lenovo T450 (i5-5300U, 8 GB) |
| RAM at peak (server + model) | ~2.1 GB |
| Model load time | ~50 s |
| Prompt processing | ~17.8 tok/s (427 tokens) |
| Text generation | ~4.04 tok/s (256 tokens) |
| First token latency | ~56 s (includes prompt processing) |
| CPU usage (peak) | ~95% |
| Thermal throttling | None observed (sustained 60-65 °C) |
| Frontend cold load | Instant (<1 s, static file) |

Generation speed is CPU-bound on the T450's dual-core i5-5300U. A modern laptop with higher single-core frequency would see 2-3x faster generation.

---

## Test Results

| # | Feature | What was tested | Result |
|---|---------|-----------------|--------|
| 1 | Chat (English) | "Give 3 marketing tips for an offline AI app" | 3 structured tips generated offline |
| 2 | Chat (Hausa) | "Ka ba ni shawarwari uku don tallata kasuwanci" | 3 Hausa-language recommendations generated |
| 3 | Task Scheduler | Add, edit, delete tasks; AI reprioritize | CRUD works, AI adjusts priority order |
| 4 | Data Analyst | CSV upload (100+ rows), bar chart, AI analysis | Chart renders, AI identifies trends |
| 5 | Knowledge Base | Upload .md file, chunk, query via chat | Chunks matched, context injected into prompt |
| 6 | Financial Analyst | NGN 500k gross / 180k expenses, CFO report | Correct profit calc, 3 strategic recommendations |

Screenshots in `Project Reports/` folder.

---

## Development Approach

The project was built using OpenCode CLI, an open-source AI coding assistant. The process involved iterative refinement across three major architectures:

1. **Gradio** (initial) — Heavy dependencies, slow cold start.
2. **FastAPI + Alpine.js + Plotly** (intermediate) — Removed Gradio but still required Python backend with pandas, sqlite-vec, etc.
3. **Pure client-side HTML + llama-server** (final) — Single `index.html` with no backend. Leanest possible: native C++ binary for AI + static HTML for UI.

The model was sourced from Cohere Labs' `tiny-aya-earth-GGUF` repository on Hugging Face, selected specifically for its strong English and Hausa language capabilities and compact 3.35B parameter size.
