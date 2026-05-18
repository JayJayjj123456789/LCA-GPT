"""LCA-GPT Enterprise — FastAPI Backend"""

import json
import logging
import os
import tempfile

import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app.analyzer import (
    analyze_enterprise_carbon,
    extract_text_from_pdf,
    find_past_audits,
    save_audit_to_memory,
)
from app.analytics import (
    carbon_breakdown_pie,
    carbon_hotspot_chart,
    carbon_sankey_diagram,
)
from app.database import get_graph_data, reset_neo4j_data, ingest_analysis_to_graph
from app.report import generate_pdf_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LCA-GPT Enterprise API",
    description="AI-Powered Supply Chain Carbon Audit & Visualization",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ───────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "LCA-GPT Enterprise API"}


# ─── Analyze ────────────────────────────────────────────────────

@app.post("/api/analyze")
async def analyze_pdf(file: UploadFile = File(...)):
    """Upload PDF, extract text, run AI carbon audit, ingest to graph."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        raw_text = extract_text_from_pdf(tmp_path)
        if not raw_text.strip():
            raise HTTPException(422, "No text extracted. The PDF may be scanned/image-based.")

        analysis_raw = analyze_enterprise_carbon(raw_text)
        if not analysis_raw:
            raise HTTPException(502, "AI returned no response")

        clean_json = analysis_raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)

        # Enrich notes with source URLs if AI didn't include them
        _enrich_notes(data)

        ingest_analysis_to_graph(data)
        save_audit_to_memory(data)

        return JSONResponse(content=data)

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        raise HTTPException(502, f"AI returned invalid JSON: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(500, str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ─── Graph ──────────────────────────────────────────────────────

@app.get("/api/graph")
async def get_graph():
    """Get supply chain graph nodes and edges from Neo4j."""
    try:
        nodes, edges = get_graph_data()
        return JSONResponse(content={"nodes": nodes, "edges": edges})
    except Exception as e:
        logger.error(f"Graph error: {e}")
        raise HTTPException(500, str(e))


@app.delete("/api/graph")
async def clear_graph():
    """Clear all data from Neo4j graph."""
    try:
        reset_neo4j_data()
        return {"status": "ok", "message": "Graph cleared"}
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Charts ─────────────────────────────────────────────────────

def _chart_to_json(fig) -> dict:
    """Convert Plotly figure to JSON-serializable dict."""
    import plotly.utils as _pu
    import json as _json
    raw = fig.to_plotly_json()
    return _json.loads(_json.dumps(raw, cls=_pu.PlotlyJSONEncoder))


@app.post("/api/charts/hotspot")
async def chart_hotspot(data: dict):
    try:
        fig = carbon_hotspot_chart(data.get("materials", []))
        return JSONResponse(content=_chart_to_json(fig))
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/charts/pie")
async def chart_pie(data: dict):
    try:
        fig = carbon_breakdown_pie(data)
        return JSONResponse(content=_chart_to_json(fig))
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/charts/sankey")
async def chart_sankey(data: dict):
    try:
        fig = carbon_sankey_diagram(data)
        return JSONResponse(content=_chart_to_json(fig))
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Report ─────────────────────────────────────────────────────

@app.post("/api/reports/pdf")
async def generate_report(data: dict):
    try:
        pdf_bytes = generate_pdf_report(data)
        project_name = data.get("project_info", {}).get("name", "report")
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="LCA_{project_name}.pdf"'
            },
        )
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Chat ───────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(payload: dict):
    question = payload.get("question", "").strip()
    if not question:
        raise HTTPException(400, "Question is required")

    try:
        from backend.graph_rag import ask_graph
        answer = ask_graph(question)
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(500, str(e))


# ─── Audits ─────────────────────────────────────────────────────

@app.get("/api/audits/similar")
async def similar_audits(materials: str = Query(...)):
    material_list = [m.strip() for m in materials.split(",") if m.strip()]
    if not material_list:
        raise HTTPException(400, "At least one material is required")

    try:
        results = find_past_audits(material_list)
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Entry Point ────────────────────────────────────────────────

def _enrich_notes(data: dict) -> None:
    """Enrich audit items with verified emission factors and trusted source URLs.

    For each material / transport item:
      1. Call search_emission_factor() — checks local fallback DB first, then Serper
         for unknown materials.
      2. If a real EF value is returned, update emission_factor + note source.
      3. Always ensure note has a trusted URL (no broken links).

    Energy items use fixed known EFs and are not sent to Serper.
    """
    from app.search import clean_note, search_emission_factor, get_trusted_source

    materials  = data.get("materials", [])
    energies   = data.get("energy", [])
    transports = data.get("transport", [])

    logger.info(
        f"Enriching: {len(materials)} materials, "
        f"{len(energies)} energy, {len(transports)} transport items"
    )

    # ── Materials: look up EF by material name ────────────────────────────────
    for m in materials:
        name = m.get("name", "")
        # Strip long parenthetical descriptions → use just the first part
        short_name = name.split("(")[0].split("—")[0].split("-")[0].strip()

        logger.info(f"  [material] Looking up EF for: '{short_name}'")
        ef_result = search_emission_factor(short_name)

        if ef_result and ef_result.value > 0:
            old_ef = m.get("emission_factor", 0)
            m["emission_factor"] = ef_result.value
            m["note"] = ef_result.source
            logger.info(
                f"    EF updated: {old_ef} → {ef_result.value} | {ef_result.source}"
            )
        else:
            # No EF found — just fix the source URL
            m["note"] = clean_note(m.get("note", ""), name, "material")

    # ── Energy: use fixed trusted EF, just clean note URL ────────────────────
    for e in energies:
        before = e.get("note", "")
        e["note"] = clean_note(before, e.get("type", ""), "energy")
        if e["note"] != before:
            logger.info(f"  [energy] '{e.get('type','')}' note fixed")

    # ── Transport: look up EF by transport mode ───────────────────────────────
    for t in transports:
        method = t.get("method", "")
        short_method = method.split("(")[0].split("—")[0].strip()

        logger.info(f"  [transport] Looking up EF for: '{short_method}'")
        ef_result = search_emission_factor(short_method)

        if ef_result and ef_result.value > 0:
            old_ef = t.get("emission_factor", 0)
            t["emission_factor"] = ef_result.value
            t["note"] = ef_result.source
            logger.info(
                f"    EF updated: {old_ef} → {ef_result.value} | {ef_result.source}"
            )
        else:
            t["note"] = clean_note(t.get("note", ""), method, "transport")


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)
