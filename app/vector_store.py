import json
import logging
import math
import os

logger = logging.getLogger(__name__)

_DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
_STORE_FILE = os.path.join(_DATA_DIR, "audits_store.json")
_FULL_FILE  = os.path.join(_DATA_DIR, "audits_full.json")

os.makedirs(_DATA_DIR, exist_ok=True)

# ── PostgreSQL storage (primary when DATABASE_URL is set) ─────────────────────

_DATABASE_URL = os.getenv("DATABASE_URL")
_PG_READY = False


def _pg_enabled() -> bool:
    return bool(_DATABASE_URL)


def _pg_conn():
    import psycopg
    return psycopg.connect(_DATABASE_URL)


def _pg_ensure() -> None:
    global _PG_READY
    if _PG_READY:
        return
    with _pg_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audits (
                id         BIGSERIAL PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                data       JSONB NOT NULL
            )
            """
        )
        # ── Multi-user migration (idempotent) ─────────────────────────────
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            BIGSERIAL PRIMARY KEY,
                email         TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token      TEXT PRIMARY KEY,
                user_email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                expires_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        conn.execute("ALTER TABLE audits ADD COLUMN IF NOT EXISTS owner_id TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audits_owner ON audits(owner_id)")
    _PG_READY = True


# ── JSON file fallback (when DATABASE_URL is unset) ───────────────────────────

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

def store_full_audit(data: dict, owner: str | None = None) -> None:
    if _pg_enabled():
        try:
            _pg_ensure()
            with _pg_conn() as conn:
                conn.execute(
                    "INSERT INTO audits (data, owner_id) VALUES (%s, %s)",
                    (json.dumps(data, ensure_ascii=False), owner),
                )
            name = data.get("project_info", {}).get("name", "Unknown")
            logger.info(f"Stored full audit '{name}' in PostgreSQL (owner={owner})")
            return
        except Exception as e:
            logger.error(f"PostgreSQL save failed, falling back to file: {e}")
    audits = _load(_FULL_FILE)
    audits.append(data)
    _save(_FULL_FILE, audits)


def get_full_audits(owner: str | None = None) -> list:
    """Return audits owned by `owner` (all audits when owner is None)."""
    if _pg_enabled():
        try:
            _pg_ensure()
            with _pg_conn() as conn:
                if owner is None:
                    rows = conn.execute(
                        "SELECT data FROM audits ORDER BY id"
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT data FROM audits WHERE owner_id = %s ORDER BY id",
                        (owner,),
                    ).fetchall()
            return [r[0] if isinstance(r[0], dict) else json.loads(r[0]) for r in rows]
        except Exception as e:
            logger.error(f"PostgreSQL read failed, falling back to file: {e}")
    return _load(_FULL_FILE)


# ── Similarity store (TF bag-of-words) ───────────────────────────────────────

def store_audit(
    project_name: str,
    summary: str,
    total_co2: float,
    materials: list[str],
) -> None:
    """Store a lightweight audit record for similarity search.

    With PostgreSQL the record is derived from the full audit at query time,
    so this is a no-op there (full audits are persisted by store_full_audit).
    """
    if _pg_enabled():
        logger.info(f"PostgreSQL mode: skipping lightweight record for '{project_name}'")
        return
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


def _records(owner: str | None = None) -> list[dict]:
    """Return similarity records, deriving them from full audits when in PG mode."""
    if _pg_enabled():
        records = []
        for d in get_full_audits(owner):
            records.append({
                "project_name": d.get("project_info", {}).get("name", "Unknown"),
                "summary":      d.get("summary", ""),
                "total_co2":    d.get("total_estimated_co2", 0),
                "materials":    [m.get("name") for m in d.get("materials", []) if m.get("name")],
            })
        return records
    return _load(_STORE_FILE)


def find_similar_audits(materials: list[str], top_k: int = 3, owner: str | None = None) -> list[dict]:
    """Find past audits using TF bag-of-words cosine similarity."""
    store = _records(owner)
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