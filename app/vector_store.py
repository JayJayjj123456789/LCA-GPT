import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "lca-audits")

# In-memory store for when Pinecone is not configured
_local_store: list[dict] = []


def store_audit(project_name: str, summary: str, total_co2: float, materials: list[str]) -> None:
    """Store an audit record for future similarity search.

    If Pinecone is configured, upsert to the cloud index.
    Otherwise, store in-memory (lost on restart).

    Args:
        project_name: Name of the project
        summary: AI-generated summary
        total_co2: Total carbon footprint (kgCO₂e)
        materials: List of material names used
    """
    record = {
        "project_name": project_name,
        "summary": summary,
        "total_co2": total_co2,
        "materials": materials,
    }

    if PINECONE_API_KEY:
        _pinecone_upsert(record)
    else:
        _local_store.append(record)
        logger.info(f"Stored audit '{project_name}' in local memory ({len(_local_store)} total)")


def find_similar_audits(materials: list[str], top_k: int = 3) -> list[dict]:
    """Find past audits with similar material profiles.

    Args:
        materials: List of material names to match against
        top_k: Maximum number of results to return

    Returns:
        List of similar audit records, sorted by relevance
    """
    if PINECONE_API_KEY:
        return _pinecone_search(materials, top_k)

    # Fallback: simple local matching by material overlap
    results = []
    material_set = set(m.lower() for m in materials)
    for record in _local_store:
        record_materials = set(m.lower() for m in record.get("materials", []))
        overlap = material_set & record_materials
        if overlap:
            results.append({
                "project_name": record["project_name"],
                "summary": record["summary"],
                "total_co2": record["total_co2"],
                "materials": record["materials"],
                "match_score": len(overlap) / max(len(material_set), 1),
            })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_k]


def _embed_text(text: str) -> list[float]:
    """Generate an embedding vector using OpenRouter (Owl-Alpha via text-embedding-3-small)."""
    import openai
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
    )
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding


def _pinecone_upsert(record: dict) -> None:
    """Upsert a record to Pinecone index with a real embedding."""
    try:
        try:
            from pinecone import Pinecone
        except ImportError:
            from pinecone_client import Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX)

        text = f"{record['project_name']} {record['summary']} {' '.join(record['materials'])}"
        vector = _embed_text(text)

        index.upsert(
            vectors=[{
                "id": record["project_name"],
                "values": vector,
                "metadata": {
                    "project_name": record["project_name"],
                    "summary": record["summary"],
                    "total_co2": record["total_co2"],
                    "materials": record["materials"],
                },
            }],
            namespace="audits",
        )
        logger.info(f"Pinecone upserted '{record['project_name']}'")
    except ImportError:
        logger.warning("pinecone-client not installed")
    except Exception as e:
        logger.error(f"Pinecone upsert failed: {e}")


def _pinecone_search(materials: list[str], top_k: int) -> list[dict]:
    """Search Pinecone for similar audits using embedding similarity."""
    try:
        try:
            from pinecone import Pinecone
        except ImportError:
            from pinecone_client import Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX)

        query_text = " ".join(materials)
        query_vector = _embed_text(query_text)

        result = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            namespace="audits",
        )

        matches = []
        for match in result.get("matches", []):
            meta = match.get("metadata", {})
            matches.append({
                "project_name": meta.get("project_name", "Unknown"),
                "summary": meta.get("summary", ""),
                "total_co2": meta.get("total_co2", 0),
                "materials": meta.get("materials", []),
                "match_score": match.get("score", 0),
            })

        logger.info(f"Pinecone found {len(matches)} similar audits for {materials}")
        return matches
    except ImportError:
        logger.warning("pinecone-client not installed")
    except Exception as e:
        logger.error(f"Pinecone search failed: {e}")
    return []
