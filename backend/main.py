"""LCA-GPT Enterprise — FastAPI Backend"""

import json
import logging
import os
import tempfile

import uvicorn
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.auth import (
    create_session,
    create_user,
    delete_session,
    find_user,
    get_session_email,
    require_user,
    validate_registration,
    verify_password,
)

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
from app.config import SECRET_DATA_KEY
from app.report import generate_pdf_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LCA-GPT Enterprise API",
    description="AI-Powered Supply Chain Carbon Audit & Visualization",
    version="1.0.0",
)

_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
if not _cors_origins:
    _cors_origins = ["http://localhost:5173", "http://localhost:8501"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ───────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "LCA-GPT Enterprise API"}


# ─── Authentication ─────────────────────────────────────────────

def _auth_payload(email: str) -> dict:
    return {"token": create_session(email), "email": email}


@app.post("/api/auth/register")
async def register(payload: dict):
    """Register a new user. The first registered user claims legacy audits."""
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    error = validate_registration(email, password)
    if error:
        raise HTTPException(400, error)
    try:
        if find_user(email):
            raise HTTPException(409, "An account with this email already exists")
        create_user(email, password)
        logger.info(f"Registered new user: {email}")
        return _auth_payload(email)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Register error: {e}")
        raise HTTPException(503, "Database not configured")


@app.post("/api/auth/login")
async def login(payload: dict):
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    user = find_user(email)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    logger.info(f"User logged in: {email}")
    return _auth_payload(email)


@app.post("/api/auth/logout")
async def logout(authorization: str = Header(None)):
    if authorization and authorization.lower().startswith("bearer "):
        delete_session(authorization.split(" ", 1)[1].strip())
    return {"status": "ok"}


@app.get("/api/auth/me")
async def me(user: str = Depends(require_user)):
    return {"email": user}


# ─── Analyze ────────────────────────────────────────────────────

def _extract_text_from_excel(file_path: str) -> str:
    """Extract text from Excel file — single read, header auto-detection."""
    import pandas as pd
    try:
        parts = []
        # CSV: single sheet, read directly
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path, header=None)
            all_sheets = {"Sheet1": df}
        else:
            all_sheets = pd.read_excel(file_path, sheet_name=None, header=None)
        for sheet_name, df in all_sheets.items():
            if df.empty:
                continue

            # Find header row — look for common column names
            header_row = None
            for i in range(min(30, len(df))):
                row_text = ' '.join(str(v).lower() for v in df.iloc[i] if pd.notna(v))
                if any(kw in row_text for kw in ['description', 'material', 'item', 'product', 'qty', 'quantity', 'amount', 'unit', 'price', 'total', 'emission', 'factor', 'scope']):
                    header_row = i
                    break

            parts.append(f"## Sheet: {sheet_name}")

            if header_row is not None:
                # Use detected header row
                header = df.iloc[header_row].tolist()
                data = df.iloc[header_row + 1:].copy()
                data.columns = header
                data = data.dropna(how='all')
                parts.append(data.to_string(index=False))
            else:
                # No header found — dump all non-empty rows
                for i in range(len(df)):
                    row_vals = [str(v) for v in df.iloc[i] if pd.notna(v)]
                    if row_vals:
                        parts.append(' | '.join(row_vals))
            parts.append("")
        return "\n".join(parts)
    except Exception as e:
        raise RuntimeError(f"Excel extraction error: {e}")


@app.post("/api/analyze")
async def analyze_file(file: UploadFile = File(...), user: str = Depends(require_user)):
    """Upload PDF or Excel, extract text, run AI carbon audit, ingest to graph."""
    fname = (file.filename or "").lower()
    if not fname:
        raise HTTPException(400, "No file provided")

    is_pdf = fname.endswith(".pdf")
    is_excel = fname.endswith((".xlsx", ".xls", ".csv"))
    if not is_pdf and not is_excel:
        raise HTTPException(400, "Only PDF and Excel (.xlsx, .xls, .csv) files are accepted")

    suffix = ".pdf" if is_pdf else (".csv" if fname.endswith(".csv") else ".xlsx")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Extract text based on file type
        if is_excel:
            raw_text = _extract_text_from_excel(tmp_path)
        else:
            raw_text = extract_text_from_pdf(tmp_path)

        if not raw_text.strip():
            raise HTTPException(422, "No text extracted. The file may be empty.")

        analysis_raw = analyze_enterprise_carbon(raw_text)
        if not analysis_raw:
            raise HTTPException(502, "AI returned no response")

        data = json.loads(analysis_raw)

        # Enrich notes with source URLs if AI didn't include them
        _enrich_notes(data)

        # Recalculate total_estimated_co2 using the updated emission factors
        # so it matches what the Matrix LCA (h = Q·B·A⁻¹·f) will compute.
        _recalculate_total_co2(data)

        save_audit_to_memory(data, user)
        try:
            from app.vector_store import store_full_audit
            store_full_audit(data, owner=user)
        except Exception as store_err:
            logger.warning(f"Vector store save failed (non-fatal): {store_err}")

        # Clear chat cache when new audit is uploaded
        from backend.cache import clear_cache
        clear_cache()
        logger.info("Chat cache cleared after new audit upload")

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


# ─── Audits ─────────────────────────────────────────────────────

@app.get("/api/audits")
async def list_audits(user: str = Depends(require_user)):
    """List all stored audits, newest first."""
    try:
        from app.vector_store import get_full_audits
        audits = get_full_audits(user)
        return JSONResponse(content=list(reversed(audits)))
    except Exception as e:
        logger.error(f"List audits error: {e}")
        raise HTTPException(500, str(e))


@app.get("/api/audits/meta")
async def list_audit_meta(user: str = Depends(require_user)):
    """List audit ids + dates for the current user (newest first)."""
    try:
        from app.vector_store import _pg_enabled, _pg_ensure, _pg_conn
        if not _pg_enabled():
            return JSONResponse(content=[])
        _pg_ensure()
        with _pg_conn() as conn:
            rows = conn.execute(
                "SELECT id, created_at, data FROM audits WHERE owner_id = %s "
                "ORDER BY id DESC",
                (user,),
            ).fetchall()
        meta = []
        for r in rows:
            d = r[2] if isinstance(r[2], dict) else json.loads(r[2])
            meta.append({
                "id": r[0],
                "created_at": r[1].isoformat() if r[1] else None,
                "name": d.get("project_info", {}).get("name", "Untitled"),
            })
        return JSONResponse(content=meta)
    except Exception as e:
        logger.error(f"List audit meta error: {e}")
        raise HTTPException(500, str(e))


@app.delete("/api/audits")
async def delete_all_audits(user: str = Depends(require_user)):
    """Permanently delete all audits owned by the current user."""
    try:
        from app.vector_store import _pg_enabled, _pg_ensure, _pg_conn
        if not _pg_enabled():
            return {"status": "ok", "deleted": 0}
        _pg_ensure()
        with _pg_conn() as conn:
            cur = conn.execute(
                "DELETE FROM audits WHERE owner_id = %s", (user,)
            )
            conn.commit()
            deleted = cur.rowcount
        logger.info(f"User {user} deleted {deleted} audit(s)")
        return {"status": "ok", "deleted": deleted}
    except Exception as e:
        logger.error(f"Delete audits error: {e}")
        raise HTTPException(500, str(e))


@app.delete("/api/audits/{audit_id}")
async def delete_audit(audit_id: int, user: str = Depends(require_user)):
    """Permanently delete a single audit owned by the current user."""
    try:
        from app.vector_store import _pg_enabled, _pg_ensure, _pg_conn
        if not _pg_enabled():
            return {"status": "ok", "deleted": 0}
        _pg_ensure()
        with _pg_conn() as conn:
            cur = conn.execute(
                "DELETE FROM audits WHERE id = %s AND owner_id = %s",
                (audit_id, user),
            )
            conn.commit()
            deleted = cur.rowcount
        if not deleted:
            raise HTTPException(404, "Audit not found")
        logger.info(f"User {user} deleted audit #{audit_id}")
        return {"status": "ok", "deleted": deleted}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete audit error: {e}")
        raise HTTPException(500, str(e))


@app.get("/api/audits/similar")
async def similar_audits(materials: str = Query(...), user: str = Depends(require_user)):
    material_list = [m.strip() for m in materials.split(",") if m.strip()]
    if not material_list:
        raise HTTPException(400, "At least one material is required")

    try:
        results = find_past_audits(material_list, owner=user)
        return JSONResponse(content=results)
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
async def chart_hotspot(data: dict, user: str = Depends(require_user)):
    try:
        fig = carbon_hotspot_chart(data.get("materials", []))
        return JSONResponse(content=_chart_to_json(fig))
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/charts/pie")
async def chart_pie(data: dict, user: str = Depends(require_user)):
    try:
        fig = carbon_breakdown_pie(data)
        return JSONResponse(content=_chart_to_json(fig))
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/charts/sankey")
async def chart_sankey(data: dict, user: str = Depends(require_user)):
    try:
        fig = carbon_sankey_diagram(data)
        return JSONResponse(content=_chart_to_json(fig))
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Report ─────────────────────────────────────────────────────

@app.post("/api/reports/pdf")
async def generate_report(data: dict, user: str = Depends(require_user)):
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
async def chat(payload: dict, user: str = Depends(require_user)):
    question = payload.get("question", "").strip()
    if not question:
        raise HTTPException(400, "Question is required")

    try:
        from backend.graph_rag import ask_graph
        answer = ask_graph(question, owner=user)
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(500, str(e))


# ─── Mathematical Analysis ──────────────────────────────────────

@app.post("/api/math/matrix-lca")
async def matrix_lca_analysis(data: dict, user: str = Depends(require_user)):
    """Run full Heijungs matrix LCA: h = Q·B·A⁻¹·f"""
    try:
        from app.math.matrix_lca import TechnologyMatrix
        tm = TechnologyMatrix.from_supply_chain(data)
        result = tm.compute_default()
        return JSONResponse(content=result.to_dict())
    except Exception as e:
        logger.error(f"Matrix LCA error: {e}")
        raise HTTPException(500, str(e))


@app.post("/api/math/leontief")
async def leontief_analysis(data: dict, user: str = Depends(require_user)):
    """Run Leontief EEIO-LCA: x = (I-A)⁻¹·y with power series visualization."""
    try:
        from app.math.leontief import LeontiefModel
        model = LeontiefModel.from_supply_chain(data)

        # Build demand vector
        items = data.get("materials", []) + data.get("energy", []) + data.get("transport", [])
        import numpy as np
        demand = np.zeros(len(items), dtype=np.float64)
        for i, item in enumerate(items):
            demand[i] = item.get("amount", 0) or item.get("usage", 0) or item.get("distance", 0)

        result = model.compute_impact(demand)
        power_series = model.power_series_approximation(demand, order=8)

        return JSONResponse(content={
            **result.to_dict(),
            "power_series": power_series,
        })
    except Exception as e:
        logger.error(f"Leontief error: {e}")
        raise HTTPException(500, str(e))


@app.post("/api/math/topsis")
async def topsis_analysis(payload: dict, user: str = Depends(require_user)):
    """Run TOPSIS multi-criteria decision analysis."""
    try:
        from app.math.topsis import TOPSIS
        topsis = TOPSIS()

        mode = payload.get("mode", "suppliers")
        if mode == "suppliers":
            result = topsis.rank_suppliers(
                payload.get("suppliers", []),
                payload.get("weights"),
            )
        elif mode == "materials":
            result = topsis.rank_materials(
                payload.get("materials", []),
                payload.get("weights"),
            )
        else:
            import numpy as np
            result = topsis.rank(
                alternatives=payload["alternatives"],
                criteria=payload["criteria"],
                decision_matrix=np.array(payload["decision_matrix"]),
                weights=payload["weights"],
                criteria_types=payload["criteria_types"],
            )

        return JSONResponse(content=result.to_dict())
    except Exception as e:
        logger.error(f"TOPSIS error: {e}")
        raise HTTPException(500, str(e))


@app.post("/api/math/monte-carlo")
async def monte_carlo_analysis(data: dict, user: str = Depends(require_user)):
    """Run full-chain Monte Carlo uncertainty propagation."""
    try:
        from app.math.matrix_lca import TechnologyMatrix
        from app.math.uncertainty import MonteCarloSimulation

        tm = TechnologyMatrix.from_supply_chain(data)
        mc = MonteCarloSimulation(tm)
        mc.set_auto_uncertainty(cv=data.get("cv", 0.15))

        n_sim = min(data.get("n_simulations", 5000), 50000)
        result = mc.simulate(tm._default_demand, n_sim=n_sim, seed=42)

        return JSONResponse(content=result.to_dict())
    except Exception as e:
        logger.error(f"Monte Carlo error: {e}")
        raise HTTPException(500, str(e))


@app.post("/api/math/sensitivity")
async def sensitivity_analysis(data: dict, user: str = Depends(require_user)):
    """Run perturbation-based sensitivity analysis."""
    try:
        from app.math.matrix_lca import TechnologyMatrix
        from app.math.sensitivity import SensitivityAnalysis

        tm = TechnologyMatrix.from_supply_chain(data)
        sa = SensitivityAnalysis()
        process_names = [p.name for p in tm.processes]
        result = sa.analyze(
            tm.A, tm.B, tm.Q, tm._default_demand,
            process_names=process_names,
            variation=data.get("variation", 0.10),
        )

        return JSONResponse(content=result.to_dict())
    except Exception as e:
        logger.error(f"Sensitivity error: {e}")
        raise HTTPException(500, str(e))


@app.post("/api/math/nonlinear")
async def nonlinear_comparison(data: dict, user: str = Depends(require_user)):
    """Compare linear vs non-linear LCA models."""
    try:
        from app.math.matrix_lca import TechnologyMatrix
        from app.math.nonlinear_lca import NonLinearLCA

        tm = TechnologyMatrix.from_supply_chain(data)
        nl = NonLinearLCA.from_technology_matrix(tm)
        comparison = nl.compare_linear_vs_nonlinear(tm.B, tm.Q, tm._default_demand)

        return JSONResponse(content=comparison)
    except Exception as e:
        logger.error(f"Non-linear error: {e}")
        raise HTTPException(500, str(e))


# ─── Advanced Charts ────────────────────────────────────────────

@app.post("/api/charts/tornado")
async def chart_tornado(data: dict, user: str = Depends(require_user)):
    """Generate tornado sensitivity chart."""
    try:
        from app.math.matrix_lca import TechnologyMatrix
        from app.math.sensitivity import SensitivityAnalysis
        from app.analytics_advanced import tornado_chart

        tm = TechnologyMatrix.from_supply_chain(data)
        sa = SensitivityAnalysis()
        tornado_data = sa.tornado_chart_data(
            tm.A, tm.B, tm.Q, tm._default_demand,
            process_names=[p.name for p in tm.processes],
        )
        fig = tornado_chart(tornado_data)
        return JSONResponse(content=_chart_to_json(fig))
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/charts/monte-carlo")
async def chart_monte_carlo(data: dict, user: str = Depends(require_user)):
    """Generate Monte Carlo histogram chart."""
    try:
        from app.math.matrix_lca import TechnologyMatrix
        from app.math.uncertainty import MonteCarloSimulation
        from app.analytics_advanced import monte_carlo_histogram

        tm = TechnologyMatrix.from_supply_chain(data)
        mc = MonteCarloSimulation(tm)
        mc.set_auto_uncertainty(cv=0.15)
        result = mc.simulate(tm._default_demand, n_sim=5000, seed=42)

        fig = monte_carlo_histogram(
            result.distribution, result.mean, result.ci_95
        )
        return JSONResponse(content=_chart_to_json(fig))
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/charts/waterfall")
async def chart_waterfall(data: dict, user: str = Depends(require_user)):
    """Generate waterfall contribution chart."""
    try:
        from app.math.matrix_lca import TechnologyMatrix
        from app.math.sensitivity import SensitivityAnalysis
        from app.analytics_advanced import waterfall_chart

        tm = TechnologyMatrix.from_supply_chain(data)
        sa = SensitivityAnalysis()
        contribs = sa.contribution_analysis(
            tm.A, tm.B, tm.Q, tm._default_demand,
            process_names=[p.name for p in tm.processes],
        )
        fig = waterfall_chart(contribs)
        return JSONResponse(content=_chart_to_json(fig))
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Entry Point ────────────────────────────────────────────────

def _merge_duplicate_energy(energies: list[dict]) -> list[dict]:
    """Merge energy items that are variations of the same type (e.g. Server Operation + Switch Operation → Electricity)."""
    if len(energies) <= 1:
        return energies

    # Group by base energy type
    groups: dict[str, list[dict]] = {}
    for e in energies:
        etype = e.get("type", "").lower()
        # Normalize: extract base type
        if any(kw in etype for kw in ['electricity', 'grid', 'power', 'kwh']):
            base = 'Electricity'
        elif any(kw in etype for kw in ['diesel', 'fuel', 'gasoline']):
            base = 'Diesel'
        elif any(kw in etype for kw in ['natural gas', 'lpg', 'lng']):
            base = 'Natural Gas'
        else:
            base = e.get("type", "Energy")
        groups.setdefault(base, []).append(e)

    merged = []
    for base, items in groups.items():
        if len(items) == 1:
            merged.append(items[0])
        else:
            # Sum usage, keep first EF, merge notes
            total_usage = sum(e.get("usage", 0) for e in items)
            ef = items[0].get("emission_factor", 0)
            unit = items[0].get("unit", "kWh")
            merged.append({
                "type": f"{base} (combined)",
                "usage": total_usage,
                "unit": unit,
                "emission_factor": ef,
                "note": f"Source: Combined from {len(items)} energy items — {items[0].get('note', '')}",
            })
            logger.info(f"Merged {len(items)} energy items → '{base} (combined)', total usage: {total_usage}")
    return merged


def _recalculate_total_co2(data: dict) -> None:
    """Recalculate total_estimated_co2 from the (possibly enriched) emission factors.

    The LLM's original total is stale after _enrich_notes() updates EFs.
    This ensures total_estimated_co2 == sum(amount * ef) across all items,
    which is the same formula the Matrix LCA (h = Q·B·A⁻¹·f with A=I) uses.
    """
    total = 0.0
    for m in data.get("materials", []):
        total += (m.get("amount") or 0) * (m.get("emission_factor") or 0)
    for e in data.get("energy", []):
        total += (e.get("usage") or 0) * (e.get("emission_factor") or 0)
    for t in data.get("transport", []):
        total += (t.get("distance") or 0) * (t.get("emission_factor") or 0)
    data["total_estimated_co2"] = round(total, 4)
    logger.info(f"Recalculated total_estimated_co2 = {data['total_estimated_co2']} kg CO₂-eq")


def _enrich_notes(data: dict) -> None:
    """Enrich audit items with verified emission factors and trusted source URLs.

    For each material / energy / transport item:
      1. Call search_emission_factor() — checks local fallback DB first (exact
         + fuzzy name matching), then Serper for unknown materials.
      2. If a real EF value is returned, update emission_factor + note source.
      3. Always ensure note has a trusted URL (no broken links).

    Energy items are merged if duplicates before the EF lookup.
    """
    from app.search import clean_note, search_emission_factor, get_trusted_source

    materials  = data.get("materials", [])
    energies   = _merge_duplicate_energy(data.get("energy", []))
    transports = data.get("transport", [])

    # Update energy in data with merged version
    data["energy"] = energies

    logger.info(
        f"Enriching: {len(materials)} materials, "
        f"{len(energies)} energy, {len(transports)} transport items"
    )

    # ── Materials: look up EF by material name ────────────────────────────────
    for m in materials:
        name = m.get("name", "")

        logger.info(f"  [material] Looking up EF for: '{name}'")
        ef_result = search_emission_factor(name)

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

    # ── Energy: look up EF by energy type (falls back to fixed known EFs) ────
    for e in energies:
        etype = e.get("type", "")
        logger.info(f"  [energy] Looking up EF for: '{etype}'")
        ef_result = search_emission_factor(etype)

        if ef_result and ef_result.value > 0:
            old_ef = e.get("emission_factor", 0)
            e["emission_factor"] = ef_result.value
            e["note"] = ef_result.source
            logger.info(
                f"    EF updated: {old_ef} → {ef_result.value} | {ef_result.source}"
            )
        else:
            before = e.get("note", "")
            e["note"] = clean_note(before, etype, "energy")
            if e["note"] != before:
                logger.info(f"  [energy] '{etype}' note fixed")

    # ── Transport: look up EF by transport mode ───────────────────────────────
    for t in transports:
        method = t.get("method", "")

        logger.info(f"  [transport] Looking up EF for: '{method}'")
        ef_result = search_emission_factor(method)

        if ef_result and ef_result.value > 0:
            old_ef = t.get("emission_factor", 0)
            t["emission_factor"] = ef_result.value
            t["note"] = ef_result.source
            logger.info(
                f"    EF updated: {old_ef} → {ef_result.value} | {ef_result.source}"
            )
        else:
            t["note"] = clean_note(t.get("note", ""), method, "transport")


# ─── Static frontend (production) ───────────────────────────────────

_DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


# ─── Secret database viewer ─────────────────────────────────────────
# Enabled only when SECRET_DATA_KEY is configured on the server.

def _secret_key_ok(key: str) -> bool:
    from secrets import compare_digest
    return bool(SECRET_DATA_KEY) and compare_digest(key or "", SECRET_DATA_KEY)


@app.get("/api/secret/audits")
async def secret_audits(key: str = Query("")):
    """Return all stored audits (with id + created_at). Requires secret key."""
    if not _secret_key_ok(key):
        raise HTTPException(404, "Not found")
    try:
        from app.vector_store import _pg_enabled, _pg_ensure, _pg_conn
        import json as _json
        if not _pg_enabled():
            return JSONResponse(content={"count": 0, "audits": []})
        _pg_ensure()
        with _pg_conn() as conn:
            rows = conn.execute(
                "SELECT id, created_at, data FROM audits ORDER BY id DESC"
            ).fetchall()
        audits = [{
            "id": r[0],
            "created_at": r[1].isoformat() if r[1] else None,
            "data": r[2] if isinstance(r[2], dict) else _json.loads(r[2]),
        } for r in rows]
        return JSONResponse(content={"count": len(audits), "audits": audits})
    except Exception as e:
        logger.error(f"Secret audits error: {e}")
        raise HTTPException(500, str(e))


@app.get("/db-view", include_in_schema=False)
async def db_view_page():
    """Secret database viewer page (looks like the frontend)."""
    page = os.path.join(os.path.dirname(__file__), "static", "db_view.html")
    if not os.path.isfile(page):
        raise HTTPException(404, "Not found")
    return FileResponse(page)


if os.path.isdir(_DIST_DIR):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(_DIST_DIR, "assets")),
        name="assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve built frontend; SPA fallback to index.html for non-API routes."""
        if full_path.startswith("api/"):
            raise HTTPException(404, "Not found")
        candidate = os.path.join(_DIST_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_DIST_DIR, "index.html"))
    logger.info(f"Static frontend mounted from {_DIST_DIR}")


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)
