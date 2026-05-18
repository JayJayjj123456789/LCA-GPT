"""LCA-GPT — Standalone LCA Analyzer (Drone Project)"""

import logging
import os

import fitz
import openai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def analyze_drone_lca(pdf_path: str) -> str:
    """Analyze a drone project PDF for LCA impact factors."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        raise RuntimeError(f"PDF read error: {e}")

    prompt = f"""
    จากรายงานโครงงานโดรน Smart Pilot-X นี้ จงวิเคราะห์ปัจจัยที่เกี่ยวข้องกับ Carbon Footprint
    และ LCA (Life Cycle Assessment) โดยเน้นไปที่:
    1. วัสดุที่ใช้ (เช่น โครงสร้างโดรน)
    2. พลังงานที่ใช้ (การใช้พลังงานที่เพิ่มขึ้นจากน้ำหนัก)
    3. ประโยชน์ในการลด Carbon (การลดจราจรบนถนน)

    ตอบกลับเป็น JSON เท่านั้นในรูปแบบ:
    {{
      "impact_factors": [{{ "item": "ชื่อปัจจัย", "description": "รายละเอียด", "impact_level": "High/Medium/Low" }}],
      "carbon_savings": {{ "cause": "สาเหตุที่ลด", "detail": "รายละเอียดการลด CO2" }}
    }}

    เนื้อหา: {text[:4000]}
    """

    try:
        response = _client.chat.completions.create(
            model="openrouter/owl-alpha",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error("AI analysis failed: %s", e)
        raise RuntimeError(f"API error: {e}")
