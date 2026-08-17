# LCA-GPT Enterprise — System Architecture

> AI-Powered Supply Chain Carbon Audit & Visualization

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Full System Flow](#full-system-flow)
5. [Step 1 — File Upload](#step-1--file-upload)
6. [Step 2 — Backend Analysis Pipeline](#step-2--backend-analysis-pipeline)
7. [Step 3 — Frontend Renders Results](#step-3--frontend-renders-results)
8. [Step 4 — Chat (Graph RAG)](#step-4--chat-graph-rag)
9. [Step 5 — Math Models](#step-5--math-models)
10. [API Endpoints](#api-endpoints)
11. [External Services](#external-services)
12. [Data Persistence](#data-persistence)
13. [Data Files Explained](#data-files-explained)

---

## Overview

LCA-GPT Enterprise reads supply chain documents (PDF, Excel, CSV), uses an LLM to extract carbon footprint data, stores results in PostgreSQL (Neon), and presents everything through an interactive React dashboard. Users can chat with their audit data via AI, run advanced mathematical LCA models, and export ISO 14067-compliant PDF reports.

**Core formula:** `CO₂e = Σ (Activity × Emission Factor)`

**Compliance standards:** ISO 14067 · GHG Protocol · GLEC Framework v3 · IPCC AR6 WG3

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite 6 + TypeScript + Tailwind CSS 4 |
| Charts | Plotly.js (react-plotly.js) |
| Graph Viz | ReactFlow |
| Backend | FastAPI + Uvicorn (Python) |
| LLM (primary) | Groq — `openai/gpt-oss-120b` |
| LLM (fallback) | OpenRouter — `poolside/laguna-s-2.1:free` |
| Database | PostgreSQL (Neon, serverless) |
| Web Search | Serper.dev (Google Search API) |
| PDF Parsing | PyMuPDF (fitz) |
| Excel/CSV Parsing | pandas |
| PDF Reports | ReportLab (ISO 14067) |
| Math / LCA | NumPy + SciPy (matrix LCA, Leontief, TOPSIS, Monte Carlo) |

---

## Project Structure

```
LCA-GPT/
├── app/                        # Core Python business logic
│   ├── config.py               # Env vars + LLM provider selection (Groq → OpenRouter)
│   ├── auth.py                 # Multi-user auth (register/login/sessions)
│   ├── analyzer.py             # PDF/Excel text extraction + LLM analysis
│   ├── analytics.py            # Basic Plotly charts (hotspot, pie, sankey)
│   ├── analytics_advanced.py   # Advanced charts (tornado, waterfall, Monte Carlo)
│   ├── report.py               # PDF report generation (ReportLab / ISO 14067)
│   ├── search.py               # Serper.dev EF lookup + 40+ material fallback DB
│   ├── vector_store.py         # PostgreSQL audit storage + similarity search
│   └── math/
│       ├── matrix_lca.py       # Heijungs matrix LCA: h = Q·B·A⁻¹·f
│       ├── leontief.py         # Leontief EEIO-LCA: x = (I−A)⁻¹·y
│       ├── topsis.py           # TOPSIS multi-criteria decision analysis
│       ├── sensitivity.py      # Perturbation-based sensitivity analysis
│       ├── nonlinear_lca.py    # Linear vs non-linear LCA comparison
│       └── uncertainty.py      # Monte Carlo uncertainty propagation
├── backend/
│   ├── main.py                 # FastAPI entry point — all API routes
│   ├── graph_rag.py            # AI chat over the user's stored audits
│   └── cache.py                # In-memory MD5-keyed response cache
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Root layout + routing + shared state
│   │   ├── api.ts              # Axios API client (fully typed)
│   │   ├── main.tsx            # React entry point
│   │   ├── components/
│   │   │   ├── Sidebar.tsx     # Navigation + Delete Audits button
│   │   │   ├── Dashboard.tsx   # 4 KPI metric cards
│   │   │   ├── Charts.tsx      # Plotly charts (hotspot, pie, sankey, advanced)
│   │   │   ├── PdfUploader.tsx # Multi-file upload + mergeResults()
│   │   │   ├── GraphViz.tsx    # ReactFlow supply chain graph
│   │   │   ├── DataTable.tsx   # Materials/Energy/Transport tables + source URLs
│   │   │   ├── Chat.tsx        # Chat UI component
│   │   │   ├── Recommendations.tsx  # Strategic insights panel
│   │   │   └── PastAudits.tsx  # Similar audits from vector search
│   │   └── views/
│   │       ├── DashboardView.tsx   # Overview: KPIs + charts + summary
│   │       ├── AuditView.tsx       # Upload + graph topology + data table
│   │       ├── GraphView.tsx       # Full-screen ReactFlow graph
│   │       ├── StrategiesView.tsx  # Chat + recommendations
│   │       ├── ReportsView.tsx     # Audit history + PDF export
│   │       └── LiveDemoView.tsx    # Demo mode
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts          # Proxies /api → FastAPI port 8001
├── data/
│   ├── sample_bom.xlsx         # Test input: Bill of Materials
│   ├── sample_purchase_order.pdf   # Test input: PO from EcoTech Manufacturing
│   ├── sample_purchase_order.txt   # Same PO as plain text
│   ├── sample_supply_chain.csv # Test input: multi-category supply chain
│   ├── sample_invoice.pdf      # ⚠️ WRONG FILE — Thai research report, not an invoice
│   ├── audits_store.json       # Auto-generated: embedding index (3072-dim vectors)
│   └── audits_full.json        # Auto-generated: complete audit history
├── tests/
│   ├── conftest.py
│   ├── test_analyzer.py
│   ├── test_database.py
│   ├── test_math.py
│   └── test_integration.py
├── .env                        # API keys (not in git)
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Full System Flow

```
User (Browser: http://localhost:5173)
        │
        │  React 19 + Vite + TypeScript + Tailwind
        │
   [Sidebar] ──────── [Main Content: 6 Views] ──────── [App.tsx State]
   Navigation         Dashboard                         analysis: AnalysisData
   + Clear DB         Audit                             audits: AnalysisData[]
                      Graph
                      Strategies
                      Reports
                      Live Demo
        │
        │  axios /api/* → Vite proxy → FastAPI :8001
        │
   FastAPI Backend (http://localhost:8001)
        │
        ├── LLM (Groq / OpenRouter)
        ├── PostgreSQL (Neon — audits, users, sessions)
        └── Serper.dev (Google Search)
```

---

## Step 1 — File Upload

The user drops one or more files into the `PdfUploader` component (Audit view).

**Accepted formats:** PDF · Excel (.xlsx, .xls) · CSV

```
User drops files into PdfUploader
        │
        ├── Multiple files?
        │   → analyze each file sequentially via POST /api/analyze
        │   → mergeResults() in browser:
        │       - deduplicate materials by name, sum amounts
        │       - deduplicate energy by type, sum usage
        │       - deduplicate transport by method, sum distance
        │       - sum total_estimated_co2
        │       - average optimization_score
        │       - union all recommendations
        │
        └── Single file → POST /api/analyze directly
```

---

## Step 2 — Backend Analysis Pipeline

```
POST /api/analyze  (multipart/form-data)
        │
        ├── PDF?    → PyMuPDF (fitz) extracts raw text from all pages
        └── Excel/CSV? → pandas reads all sheets
                         auto-detects header row (scans first 30 rows for keywords)
                         converts to text string for LLM
        │
        ▼
analyze_enterprise_carbon(text)              [app/analyzer.py]
        │
        ├── Chunk long docs (>12000 chars): first 8000 + last 4000 chars
        │
        ├── System prompt embeds:
        │   - Role: "Expert LCA Sustainability Consultant"
        │   - Per-unit EF benchmarks for 20+ electronics (laptop=350, server=1500...)
        │   - Methodology: Ecoinvent 3.9 / Thailand Grid / GLEC Framework v3
        │   - Mandatory trusted URL domains (ghgprotocol.org, ecoinvent.org, etc.)
        │   - Strict JSON-only output rule
        │
        ├── LLM call → Groq (primary) or OpenRouter (fallback)
        │   temperature: 0.1  max_tokens: 2000
        │
        └── Returns JSON string:
            {
              project_info: { name, supplier },
              materials: [{ name, amount, unit, emission_factor, note }],
              energy:    [{ type, usage, unit, emission_factor, note }],
              transport: [{ method, distance, unit, emission_factor, note }],
              total_estimated_co2: float,
              optimization_score: 0-100,
              recommendations: [string],
              summary: string
            }
        │
        ▼
_enrich_notes(data)                          [app/search.py]
        │
        ├── Materials — EF lookup:
        │   1. Check _FALLBACK_EF dict (40+ materials, instant, free)
        │   2. If unknown → Serper.dev Google Search
        │      - Parses kgCO2e value from search snippets (regex)
        │      - Validates URL against 30+ trusted domains
        │      - Caches result in memory (per process lifetime)
        │
        ├── Energy — just fix source URLs (EF stays hardcoded: 0.499 kgCO2e/kWh Thailand Grid)
        │
        └── Transport — same EF lookup as materials
        │
        ▼
store_full_audit(data, owner)                  [app/vector_store.py → PostgreSQL]
        │
        ├── INSERT JSONB row into audits (owner_id = user email)
        ├── save_audit_to_memory() → JSON file fallback
        └── Chat cache cleared on new audit
        │
        ▼
save_audit_to_memory(data)                   [app/vector_store.py]
        │
        ├── audits_store.json ← lightweight record + Gemini embedding (3072-dim)
        │   { project_name, summary, total_co2, materials: [names], embedding: [...] }
        │
        └── audits_full.json  ← complete audit JSON, no embedding
            { project_info, materials, energy, transport,
              total_estimated_co2, optimization_score, recommendations, summary }
        │
        ▼
clear_cache()                                [backend/cache.py]
Cache invalidated on every new upload so chat reflects fresh data.
        │
        ▼
Return JSON → frontend (AnalysisData)
```

---

## Step 3 — Frontend Renders Results

```
onAnalyzed(data) → App.tsx
    setAnalysis(data)
    setAudits(prev => [data, ...prev])
    setActiveView('dashboard')
        │
        ├── DashboardView
        │   ├── Dashboard.tsx     — 4 KPI cards: Supplier / Items / CO₂ / Score
        │   └── Charts.tsx        — fires 6 parallel chart API calls:
        │         POST /api/charts/hotspot     → bar chart (top emitters)
        │         POST /api/charts/pie         → emissions breakdown pie
        │         POST /api/charts/sankey      → supply chain flow
        │         POST /api/charts/tornado     → sensitivity tornado
        │         POST /api/charts/monte-carlo → MC histogram
        │         POST /api/charts/waterfall   → contribution waterfall
        │
        ├── AuditView
        │   ├── GraphViz.tsx      — GET /api/graph → ReactFlow nodes/edges
        │   └── DataTable.tsx     — materials / energy / transport tables
        │                           each row has a clickable source URL
        │
        ├── StrategiesView
        │   ├── Recommendations   — AI recommendations from audit JSON
        │   └── Chat              — POST /api/chat (Graph RAG)
        │
        └── ReportsView
            ├── Audit history list (in-memory across session)
            ├── Scope breakdown table (Materials / Energy / Transport %)
            └── Export PDF → POST /api/reports/pdf → ReportLab binary stream
```

---

## Step 4 — Chat (AI over stored audits)

```
User types question → POST /api/chat { question }
        │
ask_graph(question, owner)                     [backend/graph_rag.py]
        │
        ├── 1. Check MD5 cache → return instantly if hit (3.5s → 0.2s)
        │
        ├── 2. Load the user's audits from PostgreSQL (owner-scoped)
        │
        ├── 3. Keyword extraction from question:
        │   material  → ['material', 'steel', 'aluminum', 'วัสดุ', ...]
        │   energy    → ['energy', 'electricity', 'พลังงาน', ...]
        │   transport → ['transport', 'truck', 'ขนส่ง', ...]
        │   emission  → ['co2', 'carbon', 'คาร์บอน', ...]
        │   supplier  → ['supplier', 'ซัพพลายเออร์', ...]
        │
        ├── 4. LLM call with the relevant audit data as context:
        │   system: "Answer ONLY using audit data below. Do NOT fabricate.
        │            If not found → respond: 'ไม่มีข้อมูลนี้ใน audit ปัจจุบัน'"
        │   user:   "Audit data:\n{context}\n\nQuestion: {question}"
        │   temperature: 0.1  top_p: 0.9  frequency_penalty: 0.3  max_tokens: 800
        │   Supports Thai and English automatically
        │
        └── 5. Cache result → return answer
```

---

## Step 5 — Math Models

All math endpoints accept the same audit JSON as input.

| Endpoint | Model | Formula |
|---|---|---|
| `POST /api/math/matrix-lca` | Heijungs Matrix LCA | `h = Q·B·A⁻¹·f` |
| `POST /api/math/leontief` | Leontief EEIO-LCA | `x = (I−A)⁻¹·y` with power series |
| `POST /api/math/topsis` | TOPSIS | Multi-criteria supplier/material ranking |
| `POST /api/math/monte-carlo` | Monte Carlo | Uncertainty propagation (up to 50,000 sims) |
| `POST /api/math/sensitivity` | Perturbation Analysis | ±10% parameter variation |
| `POST /api/math/nonlinear` | Non-linear LCA | Linear vs non-linear model comparison |

**Matrix LCA pipeline (Heijungs):**
```
A ∈ ℝⁿˣⁿ  — Technology matrix (inter-process dependencies)
B ∈ ℝᵐˣⁿ  — Biosphere matrix (emissions per unit activity)
Q ∈ ℝᵖˣᵐ  — Characterization matrix (emission → impact, e.g. GWP-100)
f ∈ ℝⁿ    — Final demand vector

s = A⁻¹·f       Scaling vector
g = B·s          Raw emissions inventory (LCI)
h = Q·g          Environmental impact indicators (kgCO₂-eq)
```

**TOPSIS ranking (supplier selection):**
```
Criteria:   Carbon (40%) · Cost (30%) · Lead Time (20%) · Quality (10%)
Steps:      1. Normalize  2. Weight  3. Ideal+ / Ideal−
            4. Euclidean distances  5. Closeness: Cᵢ = d⁻ / (d⁺ + d⁻)
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register account (first user claims legacy audits) |
| `POST` | `/api/auth/login` | Login → bearer session token |
| `GET` | `/api/auth/me` | Current session user |
| `GET` | `/api/health` | Health check |
| `POST` | `/api/analyze` | Upload file → AI audit → store in PostgreSQL |
| `GET` | `/api/audits` | List user's audits (newest first) |
| `GET` | `/api/audits/meta` | id + name + date of user's audits |
| `DELETE` | `/api/audits` | Delete all of the user's audits |
| `DELETE` | `/api/audits/{id}` | Delete one audit (owner-scoped) |
| `GET` | `/api/audits/similar` | Find similar past audits |
| `POST` | `/api/charts/hotspot` | Carbon hotspot bar chart |
| `POST` | `/api/charts/pie` | Emissions breakdown pie chart |
| `POST` | `/api/charts/sankey` | Supply chain Sankey diagram |
| `POST` | `/api/charts/tornado` | Sensitivity tornado chart |
| `POST` | `/api/charts/monte-carlo` | Monte Carlo histogram |
| `POST` | `/api/charts/waterfall` | Waterfall contribution chart |
| `POST` | `/api/reports/pdf` | Generate ISO 14067 PDF report |
| `POST` | `/api/chat` | AI chat over the user's audits |
| `GET` | `/api/secret/audits` | Admin dump (requires SECRET_DATA_KEY) |
| `POST` | `/api/math/matrix-lca` | Heijungs matrix LCA |
| `POST` | `/api/math/leontief` | Leontief EEIO-LCA |
| `POST` | `/api/math/topsis` | TOPSIS supplier ranking |
| `POST` | `/api/math/monte-carlo` | Monte Carlo uncertainty |
| `POST` | `/api/math/sensitivity` | Sensitivity analysis |
| `POST` | `/api/math/nonlinear` | Linear vs non-linear comparison |

---

## External Services

| Service | Purpose | Priority |
|---|---|---|
| **Groq** (`api.groq.com`) | LLM inference — `openai/gpt-oss-120b` | Primary |
| **OpenRouter** (`openrouter.ai`) | LLM inference — `poolside/laguna-s-2.1:free` | Fallback |
| **Neon (PostgreSQL)** | Audits, users, sessions — persistent storage | Primary DB |
| **Serper.dev** | Google Search API for real-time EF source lookup | Per material |

**LLM provider selection** (`app/config.py`):
```python
if GROQ_API_KEY:
    ACTIVE_MODEL    = "openai/gpt-oss-120b"
    ACTIVE_BASE_URL = "https://api.groq.com/openai/v1"
else:
    ACTIVE_MODEL    = "poolside/laguna-s-2.1:free"
    ACTIVE_BASE_URL = "https://openrouter.ai/api/v1"
```

---

## Data Persistence

| Storage | What | Lifetime |
|---|---|---|
| Neon (PostgreSQL, cloud) | Audits (JSONB), users, sessions | Permanent |
| `backend/cache.py` (RAM) | MD5-keyed chat responses | Until restart or new upload |
| `data/audits_store.json` | JSON-file fallback audit store (when DATABASE_URL unset) | Permanent (local file) |
| `data/audits_full.json` | Complete audit JSON history (fallback) | Permanent (local file) |

**JSON files per audit — fallback stores (used only when DATABASE_URL is unset):**

```
audits_store.json                      audits_full.json
─────────────────────────────          ─────────────────────────────────────
Used for: Similar Audits search        Used for: Chat fallback context
Keys: project_name, summary,           Keys: project_info, materials[],
      total_co2, materials[names]            energy[], transport[],
                                            total_estimated_co2,
Think: "business card"                      optimization_score,
                                            recommendations, summary
                                       Think: "full report"
```

---

## Data Files Explained

| File | Role | Action |
|---|---|---|
| `data/sample_bom.xlsx` | Bill of Materials — 5 metals/polymers with EFs | ✅ Upload to test |
| `data/sample_purchase_order.pdf` | PO from EcoTech Mfg. — 4 materials + truck + energy | ✅ Upload to test |
| `data/sample_supply_chain.csv` | 10 materials + 3 transport modes + 4 energy types | ✅ Upload to test |
| `data/sample_invoice.pdf` | ⚠️ Thai research report from NECTEC — NOT an invoice | ❌ Do not use |
| `data/audits_store.json` | Auto-generated by system after each audit | Do not edit |
| `data/audits_full.json` | Auto-generated by system after each audit | Do not edit |

---

## Running the System

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Configure environment variables
# Edit .env with your API keys (Groq, OpenRouter, Serper) and DATABASE_URL

# 3. Start the backend (FastAPI)
python -m uvicorn backend.main:app --reload --port 8001

# 4. Start the frontend (React + Vite)
cd frontend
npm install
npm run dev

# 5. Open browser
# http://localhost:5173

# 6. Run tests
python -m pytest tests/ -v
```

**API documentation:** `http://localhost:8001/docs`
