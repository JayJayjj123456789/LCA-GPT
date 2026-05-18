# 🏢 LCA-GPT Enterprise

AI-Powered Supply Chain Carbon Audit & Visualization

## ภาพรวม

LCA-GPT Enterprise คือระบบวิเคราะห์คาร์บอนฟุตพรินต์ในห่วงโซ่อุปทาน โดยใช้ AI อ่านเอกสาร PDF (ใบสั่งซื้อ, รายงานความยั่งยืน) แล้วแปลงเป็นข้อมูลกราฟใน Neo4j พร้อม Dashboard แสดงผลแบบ Interactive

## เทคโนโลยี

| ส่วนประกอบ | เทคโนโลยี |
|---|---|
| Frontend | React 19 + Vite 6 + Tailwind CSS 4 |
| Backend | FastAPI + Uvicorn |
| AI Model | Owl-Alpha (OpenRouter) |
| Database | Neo4j (Graph DB) |
| PDF Processing | PyMuPDF (fitz) |
| Graph Viz | ReactFlow |
| Charts | Plotly.js |
| Reports | ReportLab (PDF) |
| Search | Serper.dev (Google Search) |
| Vector DB | Pinecone |
| Language | Python 3.x + TypeScript |

## โครงสร้างโปรเจค

```
LCA-GPT/
├── app/                        # Python business logic
│   ├── __init__.py
│   ├── config.py               # Environment variables
│   ├── analyzer.py             # PDF extraction + AI analysis
│   ├── database.py             # Neo4j operations
│   ├── analytics.py            # Plotly charts (hotspot, pie, sankey)
│   ├── report.py               # PDF report generation (ISO 14067)
│   ├── search.py               # Serper.dev search + source attribution
│   ├── vector_store.py         # Pinecone vector DB for audit memory
│   └── style.py                # Custom CSS theme (Streamlit legacy)
├── backend/
│   ├── main.py                 # FastAPI entry point (all API routes)
│   ├── graph_rag.py            # Graph RAG chat system
│   ├── ingest_to_graph.py      # Sample data ingestion
│   ├── lca_analyzer.py         # Standalone LCA analyzer
│   └── test_run.py             # Test script
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main layout + routing
│   │   ├── api.ts              # API client (axios)
│   │   ├── index.css           # Tailwind + theme variables
│   │   └── components/
│   │       ├── Sidebar.tsx     # Navigation + admin controls
│   │       ├── Dashboard.tsx   # KPI metric cards
│   │       ├── PdfUploader.tsx # Multi-file PDF upload
│   │       ├── GraphViz.tsx    # ReactFlow supply chain graph
│   │       ├── Charts.tsx      # Plotly charts (hotspot, pie, sankey)
│   │       ├── DataTable.tsx   # Materials/Energy/Transport tables
│   │       ├── Chat.tsx        # AI Strategy Consultant chat
│   │       ├── Recommendations.tsx  # Strategic insights
│   │       └── PastAudits.tsx  # Similar past audits
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
├── tests/
│   ├── conftest.py
│   ├── test_analyzer.py
│   ├── test_database.py
│   └── test_integration.py
├── data/
│   └── sample_invoice.pdf
├── .env                        # Environment variables (not in git)
├── requirements.txt
├── pytest.ini
└── README.md
```

## เริ่มต้นใช้งาน

### 1. ติดตั้ง Dependencies

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 2. ตั้งค่า Environment Variables

สร้างไฟล์ `.env` ที่ root ของโปรเจค:

```env
# === Required ===
OPENROUTER_API_KEY=your_openrouter_key
NEO4J_URI=neo4j+ssc://your_neo4j_uri
NEO4J_USERNAME=your_username
NEO4J_PASSWORD=your_password

# === Search & Intelligence ===
SERPER_API_KEY=your_serper_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=lca-audits
```

### 3. รัน Backend (FastAPI)

```bash
python -m uvicorn backend.main:app --reload --port 8001
```

API docs: `http://localhost:8001/docs`

### 4. รัน Frontend (React + Vite)

```bash
cd frontend
npm run dev
```

เปิดเบราว์เซอร์ที่ `http://localhost:5173`

> Vite dev server proxy `/api` → FastAPI port 8001

## API Endpoints

| Method | Endpoint | รายละเอียด |
|---|---|---|
| `POST` | `/api/analyze` | อัพโหลด PDF → AI วิเคราะห์คาร์บอน |
| `GET` | `/api/graph` | ดึงข้อมูล supply chain graph |
| `DELETE` | `/api/graph` | ล้างข้อมูล Neo4j |
| `POST` | `/api/charts/hotspot` | Carbon hotspot bar chart |
| `POST` | `/api/charts/pie` | Emissions breakdown pie chart |
| `POST` | `/api/charts/sankey` | Supply chain Sankey diagram |
| `POST` | `/api/reports/pdf` | สร้าง PDF report (ISO 14067) |
| `POST` | `/api/chat` | Graph RAG chat |
| `GET` | `/api/audits/similar` | ค้นหา past audits ที่คล้ายกัน |

## การใช้งานระบบ

1. **อัพโหลด PDF** — เลือกไฟล์เอกสารได้ครั้งละหลายไฟล์ (PO, Spec Sheet, Sustainability Report)
2. **กด "Run AI Carbon Audit"** — AI จะวิเคราะห์และคำนวณ Carbon Footprint
3. **ดูผลลัพธ์:**
   - **Metrics:** Supplier, Items Tracked, Carbon Footprint, Optimization Score
   - **Graph:** Supply Chain Network Visualization (ReactFlow)
   - **Analytics:** Carbon Hotspot Bar, Breakdown Pie, Supply Chain Sankey
   - **Tables:** Materials, Energy, Logistics breakdown (พร้อม clickable source URLs)
   - **Recommendations:** คำแนะนำเชิงกลยุทธ์
4. **Export Report** — กด "Export PDF" เพื่อสร้างรายงาน ISO 14067
5. **Past Audits** — ดู audit ที่เคยทำก่อนหน้า (ค้นหาจาก material ที่คล้ายกัน)
6. **ถาม Chat** — สอบถามข้อมูลเชิงลึกผ่าน Graph RAG

## มาตรฐานอ้างอิง

- **ISO 14067** — Carbon footprint of products
- **IPCC AR6 WG3** — Greenhouse gas inventory
- **GLEC Framework v3** — Logistics emissions
- **GHG Protocol** — Corporate emissions accounting

สูตร: `CO₂e = Σ (Activity × Emission Factor)`

## Source Attribution

ทุก emission factor มีแหล่งที่มาที่ตรวจสอบได้:
- **Serper.dev** ค้นหาแหล่งที่มาจริงจาก Google Search
- **Fallback database** — URL ที่ verify แล้วสำหรับวัสดุหลัก 20+ ชนิด
- Source column ในตารางแสดงเป็น **clickable link** ที่เปิดได้จริง

## รัน Tests

```bash
# รันทั้งหมด
python -m pytest tests/ -v

# รันเฉพาะไฟล์
python -m pytest tests/test_analyzer.py -v
python -m pytest tests/test_database.py -v
python -m pytest tests/test_integration.py -v
```

## Roadmap

| Phase | สถานะ | รายละเอียด |
|---|---|---|
| 1. Foundation | ✅ | Security, modular architecture, error handling |
| 2. Testing | ✅ | Unit + integration tests (19 tests) |
| 3. Visualization | ✅ | Plotly charts (hotspot, sankey, pie) |
| 4. Reporting | ✅ | ReportLab PDF (ISO 14067 standard) |
| 5. Intelligence | ✅ | Serper.dev search, Pinecone vector DB |
| 6. Frontend | ✅ | React + Vite + FastAPI backend |
| 7. Multi-file | ✅ | Upload หลาย PDF + merge results |
| 8. Excel/Word | 🔜 | รองรับอัพโหลด Excel, Word, CSV |
| 9. Auth | 🔜 | User authentication |
| 10. Deploy | 🔜 | Docker + cloud deployment |
