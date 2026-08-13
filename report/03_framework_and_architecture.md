# บทที่ 2: กรอบแนวคิดนวัตกรรมและสถาปัตยกรรมระบบ

## 2.1 กรอบแนวคิด (Conceptual Framework)

### ภาพรวมของระบบ AI-LCA

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AI-LCA SYSTEM                                │
│                  (Life Cycle Assessment with AI)                     │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
    ┌──────────────────────────────────────────────────────────┐
    │              INPUT LAYER (Data Sources)                   │
    ├──────────────────────────────────────────────────────────┤
    │  • PDF Documents (Invoices, POs, Reports)                │
    │  • Excel/CSV Files                                        │
    │  • Manual Data Entry                                      │
    │  • API Integrations (ERP, SCM systems)                   │
    └──────────────────────────────────────────────────────────┘
                                   │
                                   ▼
    ┌──────────────────────────────────────────────────────────┐
    │         PROCESSING LAYER (AI + Mathematics)              │
    ├──────────────────────────────────────────────────────────┤
    │  1. NLP Extraction (Owl-Alpha LLM)                       │
    │  2. Matrix Construction (A, B, Q)                        │
    │  3. LCA Computation (h = Q·B·A⁻¹·f)                      │
    │  4. Uncertainty Analysis (Monte Carlo)                   │
    │  5. Decision Support (TOPSIS)                            │
    └──────────────────────────────────────────────────────────┘
                                   │
                                   ▼
    ┌──────────────────────────────────────────────────────────┐
    │          STORAGE LAYER (Database)                         │
    ├──────────────────────────────────────────────────────────┤
    │  • Neo4j Graph DB (Supply Chain Network)                 │
    │  • Pinecone Vector DB (Semantic Search)                  │
    │  • File Storage (PDF Reports)                            │
    └──────────────────────────────────────────────────────────┘
                                   │
                                   ▼
    ┌──────────────────────────────────────────────────────────┐
    │      OUTPUT LAYER (Visualization & Reports)              │
    ├──────────────────────────────────────────────────────────┤
    │  • Interactive Dashboard (React + Plotly)                │
    │  • Supply Chain Graph (ReactFlow)                        │
    │  • ISO 14067 PDF Reports                                 │
    │  • API Endpoints (JSON)                                  │
    └──────────────────────────────────────────────────────────┘
```

---

## 2.2 Data Flow (การไหลของข้อมูล)

### ขั้นตอนการทำงานแบบ End-to-End

```
[1] PDF Upload
     │
     ├─→ PyMuPDF extracts text
     │
     ▼
[2] AI Analysis (Owl-Alpha)
     │
     ├─→ Identify: Materials, Energy, Transport
     ├─→ Extract: Quantities, Units, Emission Factors
     ├─→ Search: Real sources via Serper.dev
     │
     ▼
[3] Graph Construction
     │
     ├─→ Create Nodes (Suppliers, Materials, Products)
     ├─→ Create Edges (Material flows, Dependencies)
     ├─→ Store in Neo4j
     │
     ▼
[4] Matrix Assembly
     │
     ├─→ Build Technology Matrix A
     ├─→ Build Biosphere Matrix B
     ├─→ Build Characterization Matrix Q
     ├─→ Define Demand Vector f
     │
     ▼
[5] LCA Computation
     │
     ├─→ Compute: s = A⁻¹·f
     ├─→ Compute: g = B·s
     ├─→ Compute: h = Q·g
     │
     ▼
[6] Uncertainty Analysis (Optional)
     │
     ├─→ Define distributions for parameters
     ├─→ Run Monte Carlo (10,000 iterations)
     ├─→ Output: Mean ± CI_95
     │
     ▼
[7] Decision Support (Optional)
     │
     ├─→ TOPSIS ranking of alternatives
     ├─→ Generate recommendations
     │
     ▼
[8] Output Generation
     │
     ├─→ Dashboard: KPIs, Charts, Tables
     ├─→ Graph Visualization: ReactFlow
     ├─→ PDF Report: ISO 14067 format
     └─→ Store in Vector DB for future reference
```

---

## 2.3 สถาปัตยกรรมระบบ (System Architecture)

### 3-Tier Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION TIER                            │
│                    (Frontend - React 19)                         │
├─────────────────────────────────────────────────────────────────┤
│  Components:                                                     │
│  • Dashboard.tsx      → KPI Metrics                             │
│  • GraphViz.tsx       → ReactFlow Supply Chain Network          │
│  • Charts.tsx         → Plotly Visualizations                   │
│  • DataTable.tsx      → Detailed Breakdowns                     │
│  • Chat.tsx           → Graph RAG Assistant                     │
│  • PdfUploader.tsx    → Multi-file Upload                       │
│                                                                  │
│  Technology: Vite 6 + Tailwind CSS 4 + TypeScript              │
└─────────────────────────────────────────────────────────────────┘
                              ▲ │
                              │ │ REST API (JSON)
                              │ ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION TIER                             │
│                    (Backend - FastAPI)                           │
├─────────────────────────────────────────────────────────────────┤
│  Core Modules:                                                   │
│  • analyzer.py        → PDF extraction + AI analysis            │
│  • database.py        → Neo4j operations                        │
│  • analytics.py       → Plotly chart generation                 │
│  • report.py          → PDF report with ReportLab               │
│  • search.py          → Serper.dev emission factor search       │
│  • vector_store.py    → Pinecone vector DB operations           │
│                                                                  │
│  Math Modules (app/math/):                                      │
│  • matrix_lca.py      → Heijungs Framework (A, B, Q)            │
│  • uncertainty.py     → Monte Carlo Simulation                  │
│  • topsis.py          → Multi-Criteria Decision Analysis        │
│  • leontief.py        → Input-Output LCA                        │
│  • sensitivity.py     → Perturbation Analysis                   │
│                                                                  │
│  Technology: Python 3.x + FastAPI + Uvicorn                     │
└─────────────────────────────────────────────────────────────────┘
                              ▲ │
                              │ │ Bolt Protocol / HTTP
                              │ ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA TIER                                 │
│                   (Databases & Storage)                          │
├─────────────────────────────────────────────────────────────────┤
│  1. Neo4j Graph Database                                        │
│     • Nodes: Supplier, Material, Product, Process               │
│     • Edges: SUPPLIES, PRODUCES, EMITS, FLOWS_TO                │
│     • Query: Cypher language                                    │
│                                                                  │
│  2. Pinecone Vector Database                                    │
│     • Embeddings: Sentence-BERT (384-dim)                       │
│     • Use case: Semantic search for past audits                 │
│                                                                  │
│  3. File Storage                                                │
│     • Uploaded PDFs                                             │
│     • Generated PDF reports                                     │
│                                                                  │
│  4. External APIs                                               │
│     • OpenRouter (Owl-Alpha LLM)                                │
│     • Serper.dev (Google Search)                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2.4 เทคโนโลยีหลัก (Technology Stack)

### Frontend Technologies

| เทคโนโลยี | เวอร์ชัน | หน้าที่ |
|-----------|---------|--------|
| **React** | 19 | UI Framework |
| **Vite** | 6 | Build Tool & Dev Server |
| **TypeScript** | 5.x | Type-safe JavaScript |
| **Tailwind CSS** | 4 | Utility-first CSS |
| **ReactFlow** | 11.x | Graph Visualization |
| **Plotly.js** | 2.x | Interactive Charts |
| **Axios** | 1.x | HTTP Client |

### Backend Technologies

| เทคโนโลยี | เวอร์ชัน | หน้าที่ |
|-----------|---------|--------|
| **Python** | 3.10+ | Core Language |
| **FastAPI** | 0.104+ | Web Framework |
| **Uvicorn** | 0.24+ | ASGI Server |
| **NumPy** | 1.24+ | Numerical Computing |
| **SciPy** | 1.10+ | Scientific Computing |
| **PyMuPDF (fitz)** | 1.23+ | PDF Processing |
| **ReportLab** | 4.0+ | PDF Generation |

### AI & Data Technologies

| เทคโนโลยี | หน้าที่ |
|-----------|--------|
| **Owl-Alpha** | Large Language Model (via OpenRouter) |
| **Neo4j** | Graph Database |
| **Pinecone** | Vector Database |
| **Sentence-BERT** | Text Embeddings (384-dim) |
| **Serper.dev** | Google Search API |

---

## 2.5 Mathematical Core Architecture

### Module: app/math/

```
app/math/
├── __init__.py
├── matrix_lca.py          # Heijungs & Suh Framework
│   ├── TechnologyMatrix   # Main LCA engine
│   ├── LCAResult          # Result dataclass
│   └── from_supply_chain  # Builder pattern
│
├── uncertainty.py         # Monte Carlo Simulation
│   ├── MonteCarloSimulation
│   ├── ParameterDistribution
│   └── UncertaintyResult
│
├── topsis.py             # Multi-Criteria Decision
│   ├── TOPSIS
│   ├── TOPSISResult
│   ├── rank()            # Generic ranking
│   └── rank_suppliers()  # Convenience method
│
├── leontief.py           # Input-Output LCA
│   ├── LeontiefModel
│   └── compute_leontief_inverse()
│
└── sensitivity.py        # Perturbation Analysis
    ├── SensitivityAnalysis
    └── tornado_chart_data()
```

---

## 2.6 API Endpoints

### RESTful API Design

| Method | Endpoint | Description | Input | Output |
|--------|----------|-------------|-------|--------|
| `POST` | `/api/analyze` | Run LCA analysis | PDF file(s) | JSON analysis result |
| `GET` | `/api/graph` | Get supply chain graph | - | JSON nodes & edges |
| `DELETE` | `/api/graph` | Clear graph database | - | Success message |
| `POST` | `/api/charts/hotspot` | Generate hotspot chart | Analysis data | Plotly JSON |
| `POST` | `/api/charts/pie` | Generate pie chart | Analysis data | Plotly JSON |
| `POST` | `/api/charts/sankey` | Generate Sankey diagram | Analysis data | Plotly JSON |
| `POST` | `/api/reports/pdf` | Generate ISO 14067 report | Analysis data | PDF file |
| `POST` | `/api/chat` | Graph RAG chat | User message | AI response |
| `GET` | `/api/audits/similar` | Find similar past audits | Material list | Similar audits |
| `POST` | `/api/uncertainty` | Run Monte Carlo | Analysis + distributions | Uncertainty result |
| `POST` | `/api/topsis` | Rank alternatives | Decision matrix | Rankings |

---

## 2.7 Neo4j Graph Schema

### Node Types

```cypher
// Supplier Node
(:Supplier {
  name: String,
  location: String,
  sustainability_rating: Float
})

// Material Node
(:Material {
  name: String,
  amount: Float,
  unit: String,
  emission_factor: Float,
  source_url: String
})

// Product Node
(:Product {
  name: String,
  category: String
})

// Process Node
(:Process {
  name: String,
  type: String  // extraction, manufacturing, transport
})

// Emission Node
(:Emission {
  substance: String,  // CO2, CH4, N2O
  amount: Float,
  unit: String,
  gwp_factor: Float
})
```

### Relationship Types

```cypher
// Supply Relationship
(:Supplier)-[:SUPPLIES {quantity: Float, date: Date}]->(:Material)

// Production Relationship
(:Material)-[:PRODUCES {efficiency: Float}]->(:Product)

// Flow Relationship
(:Process)-[:FLOWS_TO {carbon: Float, distance: Float}]->(:Process)

// Emission Relationship
(:Process)-[:EMITS {rate: Float}]->(:Emission)
```

---

## 2.8 Security & Performance Considerations

### Security Features (Planned)

- **Authentication:** JWT-based user authentication
- **Authorization:** Role-based access control (Admin, Analyst, Viewer)
- **API Security:** Rate limiting, CORS configuration
- **Data Privacy:** Encryption at rest and in transit

### Performance Optimizations

- **Caching:** Redis for frequently accessed data
- **Async Processing:** Background jobs for large PDFs
- **Query Optimization:** Indexed Neo4j queries
- **CDN:** Static asset delivery

---

**สรุป:** ระบบออกแบบเป็น 3-Tier Architecture ที่แยกส่วนชัดเจน มีการใช้เทคโนโลยีที่ทันสมัยและเหมาะสมกับงาน โดยเน้นความสามารถในการ Scale และ Maintain ในอนาคต
