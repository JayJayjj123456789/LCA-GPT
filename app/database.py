import logging
from neo4j import GraphDatabase
from app.config import NEO4J_URI, NEO4J_USER, NEO4J_PW

logger = logging.getLogger(__name__)


def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PW))


def reset_neo4j_data() -> bool:
    if not NEO4J_URI:
        logger.info("NEO4J_URI not configured — skipping graph reset")
        return False
    driver = None
    try:
        driver = get_driver()
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        return True
    except Exception as e:
        raise RuntimeError(f"Database Reset Error: {e}")
    finally:
        if driver:
            driver.close()


def _filter_valid(items: list[dict], key: str) -> list[dict]:
    """Remove items where the merge key is null or empty."""
    filtered = []
    for item in items:
        val = item.get(key)
        if val is None or str(val).strip() == "":
            logger.warning(f"Skipping item with null/empty '{key}': {item}")
            continue
        filtered.append(item)
    return filtered


def _sanitize_item(item: dict) -> dict:
    """Replace null values with safe defaults so Neo4j never receives null."""
    return {k: (v if v is not None else "") for k, v in item.items()}


def ingest_analysis_to_graph(json_data: dict) -> None:
    if not NEO4J_URI:
        logger.info("NEO4J_URI not configured — skipping graph ingestion")
        return
    driver = None
    try:
        raw_materials = json_data.get("materials", [])
        raw_energy = json_data.get("energy", [])
        raw_transport = json_data.get("transport", [])

        logger.info(f"RAW materials: {raw_materials}")
        logger.info(f"RAW energy: {raw_energy}")
        logger.info(f"RAW transport: {raw_transport}")

        # Filter out items with null merge keys and sanitize remaining
        materials = [_sanitize_item(m) for m in _filter_valid(raw_materials, "name")]
        energy = [_sanitize_item(e) for e in _filter_valid(raw_energy, "type")]
        transport = [_sanitize_item(t) for t in _filter_valid(raw_transport, "method")]

        logger.info(f"FILTERED materials: {materials}")
        logger.info(f"FILTERED energy: {energy}")
        logger.info(f"FILTERED transport: {transport}")

        with driver.session() as session:
            # Split into separate queries — chained UNWIND on empty list kills
            # subsequent WITH rows, silently dropping energy/transport data.
            session.run(
                """
                MERGE (p:Project {name: $proj_name})
                SET p.supplier = $supplier, p.total_co2 = $total_co2, p.score = $score
                CREATE (c:CarbonImpact {summary: $summary, timestamp: datetime()})
                MERGE (p)-[:PRODUCED_IMPACT]->(c)
                """,
                proj_name=json_data["project_info"]["name"],
                supplier=json_data["project_info"]["supplier"],
                total_co2=json_data["total_estimated_co2"],
                score=json_data["optimization_score"],
                summary=json_data["summary"],
            )
            if materials:
                session.run(
                    """
                    MATCH (p:Project {name: $proj_name})
                    UNWIND $materials AS mat
                    MERGE (m:Material {name: mat.name})
                    SET m.amount = mat.amount, m.unit = mat.unit, m.ef = mat.emission_factor, m.note = mat.note
                    MERGE (p)-[:CONSISTS_OF]->(m)
                    """,
                    proj_name=json_data["project_info"]["name"],
                    materials=materials,
                )
            if energy:
                session.run(
                    """
                    MATCH (p:Project {name: $proj_name})
                    UNWIND $energy AS en
                    CREATE (e:Energy {type: en.type})
                    SET e.usage = en.usage, e.ef = en.emission_factor, e.note = en.note
                    MERGE (p)-[:POWERED_BY]->(e)
                    """,
                    proj_name=json_data["project_info"]["name"],
                    energy=energy,
                )
            if transport:
                session.run(
                    """
                    MATCH (p:Project {name: $proj_name})
                    UNWIND $transport AS tr
                    CREATE (t:Transport {method: tr.method})
                    SET t.distance = tr.distance, t.unit = tr.unit, t.ef = tr.emission_factor, t.note = tr.note
                    MERGE (p)-[:SHIPPED_VIA]->(t)
                    """,
                    proj_name=json_data["project_info"]["name"],
                    transport=transport,
                )
    finally:
        if driver:
            driver.close()


def get_graph_data():
    """Get graph data as raw dicts (for FastAPI/React).

    Returns empty graph when Neo4j is not configured so the frontend
    falls back to building the graph from in-memory audit data.
    """
    if not NEO4J_URI:
        logger.info("NEO4J_URI not configured — returning empty graph")
        return [], []
    driver = None
    try:
        driver = get_driver()
        nodes, edges = [], []
        with driver.session() as session:
            result = session.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 200")
            node_ids = set()
            for record in result:
                for node in [record["n"], record["m"]]:
                    if node.element_id not in node_ids:
                        label = list(node.labels)[0] if node.labels else "Entity"
                        colors = {
                            "Project": "#238636",
                            "Material": "#d29922",
                            "Energy": "#f85149",
                            "Transport": "#a371f7",
                            "Recommendation": "#58a6ff",
                        }
                        color = colors.get(label, "#8b949e")
                        name = (
                            node.get("name")
                            or node.get("type")
                            or node.get("method")
                            or "Data"
                        )
                        nodes.append({
                            "id": node.element_id,
                            "label": name,
                            "size": 25,
                            "color": color,
                        })
                        node_ids.add(node.element_id)
                edges.append({
                    "source": record["n"].element_id,
                    "target": record["m"].element_id,
                    "label": record["r"].type,
                })
        return nodes, edges
    except Exception:
        return [], []
    finally:
        if driver:
            driver.close()

