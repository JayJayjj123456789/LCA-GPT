"""LCA-GPT — Graph RAG Chat System"""

import logging
import os

import openai
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

logger = logging.getLogger(__name__)

_uri = os.getenv("NEO4J_URI")
_user = os.getenv("NEO4J_USERNAME")
_password = os.getenv("NEO4J_PASSWORD")

_client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def _get_driver():
    return GraphDatabase.driver(_uri, auth=(_user, _password))


def ask_graph(question: str) -> str:
    """ถามคำถามโดยดึงบริบทจาก Graph แบบเจาะลึกรายละเอียด Property"""
    driver = _get_driver()
    try:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (n)-[r]->(m)
                RETURN n, type(r) as rel_type, m,
                       properties(n) as p_n, properties(m) as p_m
                LIMIT 200
                """
            )

            context_parts = []
            for record in result:
                n = record["n"]
                m = record["m"]
                rel = record["rel_type"]
                p_n = record["p_n"]
                p_m = record["p_m"]

                def format_node(props):
                    name = (
                        props.get("name")
                        or props.get("type")
                        or props.get("method")
                        or props.get("summary", "Unknown")
                    )
                    details = []
                    if "amount" in props:
                        details.append(f"ปริมาณ: {props['amount']}")
                    if "usage" in props:
                        details.append(f"การใช้: {props['usage']}")
                    if "distance" in props:
                        details.append(f"ระยะทาง: {props['distance']}")
                    if "unit" in props:
                        details.append(f"หน่วย: {props['unit']}")
                    detail_str = f" [{', '.join(details)}]" if details else ""
                    return f"{name}{detail_str}"

                source_desc = format_node(p_n)
                target_desc = format_node(p_m)
                context_parts.append(f"- {source_desc} --({rel})--> {target_desc}")

            context = "\n".join(context_parts)

        system_prompt = """คุณคือผู้เชี่ยวชาญด้าน Life Cycle Assessment (LCA) และระบบ Graph Intelligence
        จงตอบคำถามโดยใช้ข้อมูลจาก 'ความสัมพันธ์และคุณสมบัติของโหนดในกราฟ' ที่ให้มาอย่างละเอียด
        หากผู้ใช้ถามถึงปริมาณ หน่วย หรือระยะทาง ให้ค้นหาจากข้อมูลในวงเล็บ [...] ของแต่ละโหนด
        หากข้อมูลไม่ชัดเจน ให้แจ้งสิ่งที่พบและวิเคราะห์ตามหลักการ LCA เบื้องต้น
        ตอบเป็นภาษาไทยที่กระชับ ชัดเจน และเป็นทางการ"""

        user_content = f"บริบทจากฐานข้อมูลกราฟ:\n{context}\n\nคำถาม: {question}"

        response = _client.chat.completions.create(
            model="openrouter/owl-alpha",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return "ขออภัยครับ ระบบไม่สามารถดึงข้อมูลจากกราฟมาตอบได้ในขณะนี้"
    finally:
        driver.close()


if __name__ == "__main__":
    test_q = "ในโปรเจกต์มีการใช้วัสดุอะไรบ้าง และปริมาณเท่าไหร่?"
    print(f"❓ คำถามทดสอบ: {test_q}")
    print(ask_graph(test_q))
