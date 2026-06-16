import logging

logger = logging.getLogger(__name__)

# ponytail: in-memory store; upgrade to Pinecone/pgvector when persistence is needed
_local_store: list[dict] = []


def store_audit(project_name: str, summary: str, total_co2: float, materials: list[str]) -> None:
    """Store an audit record for future similarity search (in-memory)."""
    _local_store.append({
        "project_name": project_name,
        "summary": summary,
        "total_co2": total_co2,
        "materials": materials,
    })
    logger.info(f"Stored audit '{project_name}' in local memory ({len(_local_store)} total)")


def find_similar_audits(materials: list[str], top_k: int = 3) -> list[dict]:
    """Find past audits with similar material profiles via set overlap."""
    material_set = set(m.lower() for m in materials)
    results = []
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
