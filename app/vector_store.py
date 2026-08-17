import json
import logging
import math
import os

logger = logging.getLogger(__name__)

_DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
_STORE_FILE = os.path.join(_DATA_DIR, "audits_store.json")
_FULL_FILE  = os.path.join(_DATA_DIR, "audits_full.json")

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


# ── Full audit storage ────────────────────────────────────────────────────────

def store_full_audit(data: dict) -> None:
    audits = _load(_FULL_FILE)
    audits.append(data)
    _save(_FULL_FILE, audits)


def get_full_audits() -> list:
    return _load(_FULL_FILE)


# ── Similarity store (TF bag-of-words) ───────────────────────────────────────

def store_audit(
    project_name: str,
    summary: str,
    total_co2: float,
    materials: list[str],
) -> None:
    """Store a lightweight audit record for similarity search."""
    store = _load(_STORE_FILE)
    record = {
        "project_name": project_name,
        "summary":      summary,
        "total_co2":    total_co2,
        "materials":    materials,
    }
    store.append(record)
    _save(_STORE_FILE, store)
    logger.info(f"Stored audit '{project_name}' (total={len(store)})")


def find_similar_audits(materials: list[str], top_k: int = 3) -> list[dict]:
    """Find past audits using TF bag-of-words cosine similarity."""
    store = _load(_STORE_FILE)
    if not store:
        return []

    results = []
    for record in store:
        score = _tf_cosine(materials, record.get("materials", []))
        if score > 0:
            results.append({
                **record,
                "match_score": round(score, 4),
            })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_k]


# ── TF bag-of-words cosine ────────────────────────────────────────────────────

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
