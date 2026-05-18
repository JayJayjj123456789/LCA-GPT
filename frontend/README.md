# LCA-GPT Enterprise — React Frontend

Standalone React + Vite frontend for LCA-GPT Enterprise.

## Tech Stack

| Component | Technology |
|---|---|
| Framework | React 19 + TypeScript |
| Build | Vite 6 |
| Styling | Tailwind CSS 4 |
| Charts | Plotly.js (react-plotly.js) |
| Graph Viz | React Flow |
| HTTP Client | Axios |

## Quick Start

```bash
npm install
npm run dev
```

Open `http://localhost:5173`

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx          # Entry point
│   ├── App.tsx           # Main layout + state
│   ├── api.ts            # API client + TypeScript types
│   ├── index.css         # Tailwind + theme
│   └── components/
│       ├── Sidebar.tsx       # Admin panel + export
│       ├── Dashboard.tsx     # Metric cards
│       ├── PdfUploader.tsx   # Upload + analyze
│       ├── GraphViz.tsx      # React Flow graph
│       ├── Charts.tsx        # Plotly charts
│       ├── DataTable.tsx     # Materials/Energy/Logistics tabs
│       ├── Chat.tsx          # Strategy chat
│       ├── Recommendations.tsx
│       └── PastAudits.tsx
├── package.json
├── vite.config.ts
├── tsconfig.json
└── index.html
```

## API Proxy

Vite proxies `/api` → `http://localhost:8000` (FastAPI backend). Start both servers for full functionality.
