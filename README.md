# BusinessPilot AI — ADTC 2026 Submission

<img src="https://img.shields.io/badge/domain-corporate_enterprise-blue" alt="Domain: corporate_enterprise"/> <img src="https://img.shields.io/badge/runtime-llama.cpp-green" alt="Runtime: llama.cpp"/> <img src="https://img.shields.io/badge/model-Qwen2.5--1.5B--Instruct--Q4_K_M-orange" alt="Model: Qwen2.5-1.5B-Instruct-Q4_K_M"/>

**Team:** DroneBug Technologies  
**Track:** Africa Deep Tech Challenge 2026 — Laptop LLM  
**Domain:** Corporate Enterprise

An offline business copilot for African SMEs — runs entirely on an 8 GB RAM laptop with no GPU and no internet.

---

## Overview

BusinessPilot AI combines five workspaces into a single local application:

| Page | Purpose |
|---|---|
| **Home** | System status dashboard (model health, embedding service, knowledge base) |
| **Meetings & Tasks** | Schedule, track, and AI-prioritize tasks with native Windows notifications |
| **Chat & Knowledge Base** | Upload documents (PDF, DOCX, XLSX), convert to Markdown, query via RAG |
| **Data & Charts** | CSV upload, preview, AI-powered data analysis, interactive Plotly charts |
| **Financial Analyst** | African currency support, margin analysis, CFO-style AI recommendations |

---

## Tech Stack

| Component | Choice | Rationale |
|---|---|---|
| AI model | Qwen2.5-1.5B-Instruct Q4_K_M | Strong instruction following, fits 8 GB RAM |
| Runtime | llama.cpp (b9895) | Required by ADTC, CPU-only, no GPU |
| UI | Streamlit | Minimal overhead, single-page architecture |
| HTTP client | httpx | Async HTTP for llama-server API calls |
| Vector search | sqlite-vec | Local RAG, no separate server needed |
| Charts | Plotly | Interactive, works offline |
| Notifications | plyer | Native Win32 bindings, no polling loops |
| Document conversion | Microsoft MarkItDown | PDF/DOCX/XLSX/Images → Markdown for LLM |
| Language | Python 3.14 | Offline-first, standard library preferred |

---

## Quick Start

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Download the model weights
bash download_model.sh

# 3. Start the AI server
start_llama_server.bat

# 4. Launch the app
run_app.bat
```

Or use the all-in-one launcher:
```bash
run_business_pilot.bat
```

Then open **http://localhost:8081** in your browser.

---

## Project Structure

```
├── app.py                          # Streamlit entry point (Home page)
├── pages/
│   ├── 1_Calendar_and_Tasks.py     # Task scheduler with AI prioritization
│   ├── 2_Chat_and_RAG.py           # Document upload, conversion, RAG chat
│   ├── 3_Data_and_Charts.py        # CSV analysis + interactive charts
│   └── 4_Financial_Analyst.py      # Financial metrics, African currencies
├── utils/
│   ├── config.py                   # Environment & path configuration
│   ├── theme.py                    # Dark/light theme, CSS, UI components
│   ├── ai_engine.py                # Async llama.cpp chat & embedding client
│   └── db.py                       # sqlite-vec vector storage (RAG)
├── modules/
│   ├── task_manager.py             # Task persistence + daemon scheduler
│   ├── financial.py                # Margin/CFO analysis, African currencies
│   ├── data_analysis.py            # CSV profiling & insight prompt builder
│   ├── markitdown_skill.py         # Document → Markdown converter
│   └── notification.py             # plyer Windows notification wrapper
├── metadata.json                   # ADTC submission metadata
├── download_model.sh               # Downloads Qwen2.5-1.5B Q4_K_M
├── REPORT.md                       # Technical writeup
├── requirements.txt                # Python dependencies
├── start_llama_server.bat          # Starts llama.cpp server
├── run_app.bat                     # Starts Streamlit UI
└── run_business_pilot.bat          # All-in-one launcher
```

---

## Offline Design

- **No cloud calls** during inference — zero outbound requests after model load
- **Inline SVG icons** — no CDN dependency for UI rendering (Tabler-style paths in `theme.py`)
- **Local RAG** — sqlite-vec stores embeddings in `vectors.db`, no external vector DB
- **Scheduler** — daemon thread with native Win32 notifications via plyer
- **Document conversion** — MarkItDown fallback to manual text parsing when package absent

---

## Submission Files

| File | Status |
|---|---|
| `metadata.json` | ✅ Filled |
| `download_model.sh` | ✅ Downloads Qwen2.5-1.5B-Instruct-Q4_K_M |
| `REPORT.md` | ✅ Complete technical writeup |
| `model/.gitkeep` | ✅ Placeholder (model weights excluded via `.gitignore`) |
| `.gitignore` | ✅ Excludes `.gguf`, `__pycache__`, `tasks.json` |

---

## License

This project is licensed under the terms of the [GNU GPL v3 License](LICENSE).

