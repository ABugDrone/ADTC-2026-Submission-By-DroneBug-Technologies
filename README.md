# BusinessPilot AI — ADTC 2026 Submission

**Team:** DroneBug Technologies  
**Track:** Africa Deep Tech Challenge 2026 — Laptop LLM  
**Domain:** Corporate Enterprise  
**Languages:** English / Hausa

An offline business copilot for African SMEs — runs entirely on an 8 GB RAM laptop with no GPU and no internet. Bilingual (English + Hausa).

---

## Overview

BusinessPilot AI provides 5 workspaces in a single local application:

| Tab | Role | Purpose |
|-----|------|---------|
| **Home** | System Health | Monitor AI server status, notifications, storage |
| **Task Scheduler** | Project Manager | Add/edit/delete tasks with priority sorting, AI re-prioritization, Windows toast notifications |
| **Data Analyst** | Data Specialist | Upload CSV, preview, interactive charts (bar/line/pie/scatter), AI data insights |
| **Knowledge Base** | Business Consultant | Upload .md/.txt documents, chunk and store locally, semantic search, chat with context (EN/HA) |
| **Financial Analyst** | CFO | African currencies (NGN, KES, ZAR, GHS, EGP, USD), profit/loss calculator, bar chart, AI CFO strategic report |

---

## Quick Start

**Prerequisites:** Windows, ~2 GB free RAM, ~3 GB free disk.

```batch
run_business_pilot.bat
```

This starts two local servers:
1. **llama-server.exe** on `127.0.0.1:8083` — the AI inference engine (tiny-aya-earth Q4_K_M, 3.35B)
2. **python -m http.server** on `127.0.0.1:8081` — serves the frontend

Then opens `http://localhost:8081/` in your browser.

Or simply double-click `static/index.html` directly (requires `--ui-mcp-proxy` on llama-server for CORS).

---

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| AI model | tiny-aya-earth Q4_K_M (3.35B) | Multilingual (EN+HA), fits 8 GB RAM |
| Runtime | llama-server.exe (b9895) | CPU-only, no GPU, ADTC-compliant |
| Frontend | Single `index.html` | Zero dependencies, pure client-side |
| Charts | Chart.js 4.4.7 | Offline, lightweight (206 KB) |
| CSV parsing | PapaParse 5.4.1 | Client-side, no server needed |
| Markdown | marked.js 12.0.2 | Renders AI output as formatted text |
| Persistence | localStorage | Tasks, chat history, KB chunks survive refresh |
| Notifications | Browser Notification API | Native Windows toasts |
| Bilingual | System prompt + automatic detection | Responds in English or Hausa |

---

## Project Structure

```
├── static/
│   ├── index.html            # Single-page frontend (all 5 tabs)
│   └── libs/
│       ├── chart.umd.min.js  # Chart.js
│       ├── papaparse.min.js  # PapaParse
│       └── marked.min.js     # marked.js
├── model/
│   └── tiny-aya-earth-q4_k_m.gguf  # 3.35B GGUF model
├── llama-b9895-bin-win-cpu-x64/
│   ├── llama-server.exe      # AI server binary
│   └── llama-server-impl.dll # Server implementation
├── run_business_pilot.bat    # All-in-one launcher
├── submission.json           # ADTC submission metadata
├── TECHNICAL_REPORT.md       # Technical writeup
├── Project Reports/          # Screenshots
├── LICENSE                   # GNU GPL v3
└── README.md                 # This file
```

---

## Offline Design

- **No cloud calls** — zero outbound requests during inference
- **No Python backend** — everything runs in the browser or as native binary
- **All libraries bundled** — Chart.js, PapaParse, marked.js shipped in `static/libs/`
- **System fonts only** — no web font downloads
- **localStorage persistence** — no external database needed
- **Bilingual by default** — system prompt tells the model to reply in whatever language the user writes in

---

## Submission Files

| File | Status |
|------|--------|
| `submission.json` | ✅ ADTC metadata filled |
| `Hackathon Reports.txt` | ✅ Technical writeup |
| `Project Reports/` | ✅ Screenshots |
| `run_business_pilot.bat` | ✅ All-in-one launcher |
| `model/tiny-aya-earth-q4_k_m.gguf` | ✅ Model weights (3.35B, Q4_K_M) |
| `LICENSE` | ✅ GNU GPL v3 |

---

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).
