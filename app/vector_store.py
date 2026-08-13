import json
import logging
import math
import os

import requests

from app.config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

_DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
_STORE_FILE = os.path.join(_DATA_DIR, "audits_store.json")
_FULL_FILE  = os.path.join(_DATA_DIR, "audits_full.json")

_GEMINI_EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/{model}:embedContent"
)

os.makedirs(_DATA_DIR, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load(path: str) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save(path: str, data: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Gemini embedding ──────────────────────────────────────────────────────────

def _get_embedding(text: str) -> list[float] | None:
    """Call Gemini embedContent and return a float vector, or None on failure."""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — skipping embedding.")
        return None
    try:
        url = _GEMINI_EMBED_URL.format(model=GEMINI_EMBEDDING_MODEL)
        resp = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            json={
                "model": f"models/{GEMINI_EMBEDDING_MODEL}",
                "content": {"parts": [{"text": text}]},
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]["values"]
    except Exception as e:
        logger.error(f"Gemini embedding error: {e}")
        return None


def _cosine(v1: list[float], v2: list[float]) -> float:
    """Cosine similarity between two equal-length float vectors."""
    dot   = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def _record_text(project_name: str, summary: str, materials: list[str]) -> str:
    """Build a single string to embed for an audit record."""
    mats = ", ".join(materials) if materials else ""
    return f"{project_name}. {summary}. Materials: {mats}"


# ── Full audit storage ────────────────────────────────────────────────────────

def store_full_audit(data: dict) -> None:
    audits = _load(_FULL_FILE)
    audits.append(data)
    _save(_FULL_FILE, audits)


def get_full_audits() -> list:
    return _load(_FULL_FILE)


# ── Semantic similarity store ─────────────────────────────────────────────────

def store_audit(
    project_name: str,
    summary: str,
    total_co2: float,
    materials: list[str],
) -> None:
    """Store a lightweight audit record with its semantic embedding vector."""
    store = _load(_STORE_FILE)
    text  = _record_text(project_name, summary, materials)
    emb   = _get_embedding(text)
    record = {
        "project_name": project_name,
        "summary":      summary,
        "total_co2":    total_co2,
        "materials":    materials,
        "embedding":    emb,          # None when Gemini key absent
    }
    store.append(record)
    _save(_STORE_FILE, store)
    dim = len(emb) if emb else 0
    logger.info(f"Stored audit '{project_name}' (embedding dim={dim}, total={len(store)})")


def find_similar_audits(materials: list[str], top_k: int = 3) -> list[dict]:
    """Find past audits using cosine similarity on Gemini semantic embeddings.

    Falls back to TF bag-of-words cosine if a record has no embedding stored
    (e.g. records written before the Gemini upgrade).
    """
    store = _load(_STORE_FILE)
    if not store:
        return []

    # Build query embedding
    query_text = "Materials: " + ", ".join(materials)
    query_emb  = _get_embedding(query_text)

    results = []
    for record in store:
        rec_emb = record.get("embedding")

        if query_emb and rec_emb:
            # Semantic cosine similarity
            score = _cosine(query_emb, rec_emb)
        else:
            # Legacy TF bag-of-words fallback
            score = _tf_cosine(materials, record.get("materials", []))

        if score > 0:
            results.append({
                **{k: v for k, v in record.items() if k != "embedding"},
                "match_score": round(score, 4),
            })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_k]


# ── Legacy TF fallback (used when embedding is unavailable) ───────────────────

def _tf_vector(tokens: list[str]) -> dict[str, float]:
    from collections import Counter
    counts = Counter(t.lower() for t in tokens)
    total  = max(sum(counts.values()), 1)
    return {t: c / total for t, c in counts.items()}


def _tf_cosine(q_tokens: list[str], r_tokens: list[str]) -> float:
    v1 = _tf_vector(q_tokens)
    v2 = _tf_vector(r_tokens)
    dot   = sum(v1.get(t, 0.0) * v2.get(t, 0.0) for t in v2)
    norm1 = math.sqrt(sum(x * x for x in v1.values()))
    norm2 = math.sqrt(sum(x * x for x in v2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)
