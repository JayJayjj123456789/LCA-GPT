# 🏢 LCA-GPT Enterprise

AI-Powered Supply Chain Carbon Audit & Visualization

## ภาพรวม

LCA-GPT Enterprise คือระบบวิเคราะห์คาร์บอนฟุตพรินต์ในห่วงโซ่อุปทาน โดยใช้ AI อ่านเอกสาร PDF (ใบสั่งซื้อ, รายงานความยั่งยืน) แล้วแปลงเป็นข้อมูลกราฟใน Neo4j พร้อม Dashboard แสดงผลแบบ Interactive

## เทคโนโลยี

| ส่วนประกอบ | เทคโนโลยี |
|---|---|
| Frontend | Streamlit |
| AI Model | Owl-Alpha (OpenRouter) |
| Database | Neo4j (Graph DB) |
| PDF Processing | PyMuPDF (fitz) |
| Graph Viz | streamlit-agraph |
| Charts | Plotly |
| Reports | ReportLab |
| Search | Google Search API (stub) |
| Vector DB | Pinecone (stub) |
| Language | Python 3.x |

## โครงสร้างโปรเจค

```
LCA-GPT/
├── app.py                    # Streamlit entry point (UI + orchestration)
├── app/
│   ├── __init__.py
│   ├── config.py             # Environment variables
│   ├── analyzer.py           # PDF extraction + AI analysis
│   ├── database.py           # Neo4j operations
│   ├── analytics.py          # Plotly charts (hotspot, pie, sankey)
│   ├── report.py             # PDF report generation (ISO 14067)
│   ├── search.py             # Google Search API for EF lookup (stub)
│   ├── vector_store.py       # Pinecone vector DB for audit memory (stub)
│   └── style.py              # Custom CSS theme
├── backend/
│   ├── graph_rag.py          # Graph RAG chat system
│   ├── ingest_data.py        # Sample data ingestion
│   ├── ingest_to_graph.py    # Alternative ingestion
│   ├── lca_analyzer.py       # Standalone LCA (drone project)
│   ├── main.py               # LlamaParse extraction (experimental)
│   └── test_run.py           # Test script
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Shared fixtures
│   ├── test_analyzer.py      # Unit tests for analyzer
│   ├── test_database.py      # Unit tests for database
│   └── test_integration.py   # Integration & edge case tests
├── data/
│   └── sample_invoice.pdf
├── frontend/
│   └── README.md             # Reserved for future standalone frontend
├── requirements.txt
├── pytest.ini
└── .gitignore
```

## เริ่มต้นใช้งาน

### 1. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 2. ตั้งค่า Environment Variables

สร้างไฟล์ `backend/.env`:

```env
OPENROUTER_API_KEY=your_openrouter_key
NEO4J_URI=neo4j+ssc://your_neo4j_uri
NEO4J_USERNAME=your_username
NEO4J_PASSWORD=your_password

# Optional — Phase 5 Intelligence (stubs work without these)
# GOOGLE_API_KEY=your_google_api_key
# GOOGLE_CSE_ID=your_custom_search_engine_id
# PINECONE_API_KEY=your_pinecone_key
# PINECONE_INDEX=lca-audits
```

### 3. รันแอป

```bash
streamlit run app.py
```

เปิดเบราว์เซอร์ที่ `http://localhost:8501`

## รัน Tests

```bash
# รันทั้งหมด
python -m pytest tests/ -v

# รันเฉพาะไฟล์
python -m pytest tests/test_analyzer.py -v
python -m pytest tests/test_database.py -v
python -m pytest tests/test_integration.py -v

# รันเฉพาะ class
python -m pytest tests/test_analyzer.py::TestExtractTextFromPdf -v
```

### ผลลัพธ์ที่คาดหวัง

```
19 passed in 1.42s
```

## การใช้งานระบบ

1. **อัพโหลด PDF** — เลือกไฟล์เอกสาร (PO, Spec Sheet, Sustainability Report)
2. **กด "Run AI Carbon Audit"** — AI จะวิเคราะห์และคำนวณ Carbon Footprint
3. **ดูผลลัพธ์:**
   - Metrics: Supplier, Items Tracked, Carbon Footprint, Optimization Score
   - Graph: Supply Chain Network Visualization
   - **Analytics:** Carbon Hotspot Bar, Breakdown Pie, Supply Chain Sankey
   - Tables: Materials, Energy, Logistics breakdown
   - Recommendations: คำแนะนำเชิงกลยุทธ์
4. **Export Report** — กด "Download PDF Report" ใน sidebar เพื่อสร้างรายงาน ISO 14067
5. **Past Audits** — ดู audit ที่เคยทำก่อนหน้า (ค้นหาจาก material ที่คล้ายกัน)
6. **ถาม Chat** — สอบถามข้อมูลเชิงลึกผ่าน Graph RAG

## มาตรฐานอ้างอิง

- **ISO 14067** — Carbon footprint of products
- **IPCC 2019** — Greenhouse gas inventory
- **GLEC Framework** — Logistics emissions

สูตร: `CO₂e = Σ (Activity × Emission Factor)`

## Phase 6: Run with FastAPI + React

### Start Backend (FastAPI)

```bash
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

### Start Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Open browser at `http://localhost:5173`

> The Vite dev server proxies `/api` requests to FastAPI on port 8000.

---

## Roadmap

| Phase | สถานะ | รายละเอียด |
|---|---|---|
| 1. Foundation | ✅ เสร็จ | Security, modular architecture, error handling |
| 2. Testing | ✅ เสร็จ | Unit + integration tests (19 tests) |
| 3. Visualization | ✅ เสร็จ | Plotly charts (hotspot, sankey, pie) |
| 4. Reporting | ✅ เสร็จ | ReportLab PDF (ISO 14067 standard) |
| 5. Intelligence | ✅ เสร็จ | Google Search API stub, Pinecone vector DB stub |
| 6. Frontend | ✅ เสร็จ | React + Vite + FastAPI backend |
