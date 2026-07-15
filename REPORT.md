# Technical Report — BusinessPilot AI: Offline Business Copilot

**Team ID:** DroneBug Technologies
**Domain:** corporate_enterprise
**Model:** Qwen2.5-1.5B-Instruct-Q4_K_M

---

## Problem

African SMEs and entrepreneurs face three compounding challenges: (1) unreliable or expensive internet connectivity that clouds any SaaS business tool, (2) limited access to AI-powered business intelligence tools that require cloud subscriptions, and (3) the administrative burden of task scheduling, financial tracking, and data analysis on resource-constrained laptops. BusinessPilot AI solves this by providing a complete offline business assistant that runs entirely on a commodity 8 GB RAM laptop with no GPU, no internet, and no cloud dependency.

Target users include micro-entrepreneurs, SME owners, accountants, and operations managers across Africa who need AI-enhanced scheduling, financial modeling, CSV-based data analysis, and document Q&A — all running locally on a Lenovo T450-class machine.

---

## Design Decisions

- **Base model:** Qwen2.5-1.5B-Instruct (GGUF Q4_K_M). Chosen for its strong instruction-following ability, English proficiency, and small 1.5B parameter footprint that fits comfortably within 8 GB RAM.
- **Quantization:** Q4_K_M provides the best quality-to-RAM tradeoff. Q8_0 would exceed memory budget after loading the app stack; Q2_K degraded output quality noticeably in business reasoning tasks.
- **Runtime:** llama.cpp (b9895, Windows CPU build) — the only supported runtime per ADTC rules. No GPU required.
- **Alternatives rejected:** DeepSeek-R1-Distill-Qwen-7B was considered but at 7B Q4 it would leave insufficient headroom alongside Python + Streamlit + browser in 8 GB RAM. Phi-3-mini (3.8B) was heavier than needed for structured business tasks.
- **Application stack:** Streamlit for the UI (minimal overhead, single-page app), plyer for native Windows notifications (avoids background polling loops), and Plotly for interactive charts. No heavy frontend frameworks.
- **Vector search:** sqlite-vec provides local RAG without needing a separate vector database server.
- **Document conversion:** Microsoft MarkItDown (`markitdown` package) converts uploaded PDFs, DOCX, XLSX, and images to Markdown for LLM ingestion, with a manual text fallback when the package is unavailable.
- **Development tooling:** Kombai was used for iterative UI fixes (before/after screenshot comparison of Streamlit component styling), and OpenCode CLI for AI-assisted development workflow — both are development-time tools, not runtime dependencies.
- **Background scheduler:** A daemon thread checks task timestamps every 60 seconds against the system clock and fires native Windows notifications via plyer when an event is due. No external cron or task scheduler dependency.

---

## Constraints

- **Hardware:** Lenovo T450, 8 GB RAM, Intel Core i5-5300U (2 core/4 thread), integrated Intel HD Graphics 5500. No GPU acceleration.
- **Memory budget:** ~1.2 GB for llama.cpp + Qwen2.5-1.5B Q4_K_M, ~400 MB for Python/Streamlit/pandas, ~300 MB for OS overhead. Total ~2 GB peak — well within 8 GB.
- **Connectivity:** Fully offline during inference. Model weights downloaded once via `download_model.sh`; all subsequent operations use the local llama-server API on `127.0.0.1:8033`.
- **Power:** Designed for battery-conscious operation on a laptop. The Q4_K_M quantization reduces memory bandwidth and CPU load.
- **No cloud services:** plyer uses native Win32 API bindings; no background polling loops or cloud sync.

---

## Benchmarks

Observed on Lenovo T450 (i5-5300U, 8 GB DDR3, Windows 10, CPU-only):

| Metric | Value |
|---|---|
| Machine | Lenovo T450 (i5-5300U, 8 GB) |
| RAM at peak (app + model) | ~1.8 GB |
| Time to first token | ~480 ms |
| Generation speed | ~6.5 t/s (sustained) |
| Prompt processing | ~25 t/s |
| Thermal throttling | None observed (sustained 60-65 °C) |
| Background scheduler overhead | <0.5% CPU, negligible RAM |
| Streamlit page load | ~1.2 s cold start |
| **Self-reported Sperf** | **Sperf = 6.5** |
| **Self-reported Seff** | **Seff = 1.8GB** |

These are self-reported development benchmarks. Official scores are measured by the ADTC profiler on the standard evaluation machine.

---

## Test Results

Four functional test cases were executed on the running application (localhost:8081, 14 July 2026). Screenshots of each test are saved in `Project Reports/`.

### Test 1 — Chat & Knowledge Base (RAG)

**Query:** *"I need marketing tips on how to sell AI powered offline business apps"*

The model returned a structured 10-point response covering: unique value proposition, real-world use cases, scalability, customer feedback, free trial/demo, influencer partnerships, social media marketing, referral programs, clear pricing, and customer support. The response was generated offline via the local llama-server with no cloud calls. The RAG pipeline retrieved relevant context from the seeded knowledge base before answering.

### Test 2 — Data & Charts

Uploaded a CSV and used the interactive chart builder. The page rendered a Plotly line chart from the data with configurable X/Y axes and chart type. The "Ask the AI about this data" section was also active, allowing natural-language queries over the uploaded CSV. Chart generation ran entirely client-side with no external dependencies.

### Test 3 — Financial Analyst (Input & Metrics)

Tested with Nigerian Naira (₦) currency selected. Input figures: Revenue = ₦100,000, COGS = ₦40,000, OpEx = ₦30,000. The key metrics panel correctly computed:

| Metric | Value |
|---|---|
| Gross Profit | ₦60,000 |
| Revenue | ₦100,000 |
| Gross Margin | 60.0% |
| Net Profit | ₦30,000 |

A cost breakdown bar chart (COGS vs OpEx) was rendered using Plotly. All calculations performed locally with no cloud API.

### Test 4 — Financial Analyst (CFO Summary)

After entering financial figures, the "Generate CFO Summary" button was triggered. The model produced three actionable recommendations:

1. **Increase Productivity** — Enhance operational efficiency to reduce COGS through better inventory management, improved production processes, or more effective use of resources.
2. **Expand Market Share** — Increase sales by targeting new markets or expanding into existing markets with higher margins.
3. **Optimize Cost Structure** — Review and reduce unnecessary operating expenses, renegotiate contracts, eliminate non-essential services, or improve supplier relationships.

A Finance Chat sidebar was also available for follow-up questions about the entered financials. All responses generated offline.

---

## Screenshots

| # | Page | File | Description |
|---|---|---|---|
| 11 | Chat & Knowledge Base | `Project Reports/11.png` | RAG response to marketing tips query |
| 12 | Data & Charts | `Project Reports/12.png` | Interactive Plotly line chart from CSV |
| 13 | Financial Analyst | `Project Reports/13.png` | Nigerian Naira input with key metrics panel |
| 14 | Financial Analyst | `Project Reports/14.png` | CFO Summary recommendations and cost breakdown |
