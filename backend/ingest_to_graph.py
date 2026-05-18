"""LCA-GPT — Alternative Graph Ingestion Template"""

import logging
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
logger = logging.getLogger(__name__)


def get_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    return GraphDatabase.driver(uri, auth=(user, password))


def ingest_trainee_data(data: dict) -> None:
    """Ingest trainee/project/lab data from extracted JSON into Neo4j."""
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run(
                """
                MERGE (t:Trainee {name: $trainee_name})
                SET t.school = $school, t.level = $level
                MERGE (p:Project {name: $project_name})
                MERGE (l:Lab {name: $lab_name})
                SET l.organization = $org
                MERGE (t)-[:PARTICIPATED_IN]->(p)
                MERGE (p)-[:CONDUCTED_AT]->(l)
                """,
                trainee_name=data["trainee"]["name"],
                school=data["trainee"]["school"],
                level=data["trainee"]["level"],
                project_name=data["project_name"],
                lab_name=data["laboratory"]["lab_name"],
                org=data["laboratory"]["center"],
            )
        logger.info("Data ingested successfully")
    except Exception as e:
        logger.error("Ingestion failed: %s", e)
        raise
    finally:
        driver.close()


if __name__ == "__main__":
    # Example usage
    sample_data = {
        "trainee": {"name": "นางสาวพรลภัส", "school": "จุฬาภรณ์", "level": "ม.4"},
        "project_name": "AI Project",
        "laboratory": {"lab_name": "AIM Lab", "center": "NECTEC"},
    }
    ingest_trainee_data(sample_data)
