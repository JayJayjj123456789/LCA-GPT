import json
import fitz
import openai
import logging
from app.config import OPENROUTER_API_KEY
from app.search import search_emission_factor
from app.vector_store import store_audit, find_similar_audits

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        raise RuntimeError(f"PDF Error: {e}")
    return text


def analyze_enterprise_carbon(text: str) -> str | None:
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    content_text = text[:6000]
    system_prompt = (
        "You are an Expert LCA Sustainability Consultant. Analyze supply chain carbon footprint data strictly. "
        "Methodology: 1. Materials: TGO/Ecoinvent 3.9 2. Energy: Thailand Grid (~0.499 kgCO2e/kWh) 3. Transport: GLEC Framework v3. "
        "CRITICAL RULE: Every 'note' field MUST include a REAL, VERIFIABLE source URL. "
        "Format: 'Source: [Database] — https://[url]'. "
        "ONLY use URLs from the following verified working domains: "
        # หมวด 1: มาตรฐานสากล
        "GHG Protocol: https://ghgprotocol.org/, "
        "IPCC AR6 WG3: https://www.ipcc.ch/report/ar6/wg3/, "
        "ISO Standards: https://www.iso.org/, "
        # หมวด 2: ฐานข้อมูลคาร์บอนโลก
        "Ecoinvent: https://ecoinvent.org/database/, "
        "Climatiq: https://climatiq.io/, "
        # หมวด 3: ไทย
        "TGO Thailand: https://www.tgo.or.th, "
        "TGO Carbon Label: https://thaicarbonlabel.tgo.or.th/, "
        "DIW Thailand: https://www.diw.go.th/, "
        # หมวด 4: พลังงาน
        "IEA Emissions Factors: https://www.iea.org/data-and-statistics/data-product/emissions-factors-2023, "
        "EGAT Thailand: https://www.egat.co.th/, "
        # หมวด 5: โลจิสติกส์ — NOTE: use smartfreightcentre.org NOT glec.org
        "GLEC Framework (Smart Freight Centre): https://www.smartfreightcentre.org/en/glec/, "
        # หมวด 6: ESG
        "SET Sustainability: https://www.setsustainability.com/, "
        # หมวด 9: กฎระเบียบยุโรป
        "European Commission: https://ec.europa.eu/, "
        "European Platform LCA: https://eplca.jrc.ec.europa.eu/, "
        # รัฐบาลอื่น
        "EPA GHG Hub: https://www.epa.gov/climateleadership/ghg-emission-factors-hub, "
        "UK Gov BEIS: https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting. "
        "NEVER use glec.org — it is not a real source. Always use smartfreightcentre.org/en/glec/ for transport. "
        "NEVER fabricate or guess URLs. Return clean JSON only. No markdown."
    )
    user_prompt = f"""
    Analyze the following document for a complete Carbon Footprint / LCA audit.
    IMPORTANT: The 'note' field for EVERY item MUST follow this exact format:
    'Source: [Database Name] — https://[real-url-to-source]'

    Required JSON structure:
    {{
      "project_info": {{ "name": "Descriptive Project Name", "supplier": "Supplier/Company Name" }},
      "materials": [
        {{
          "name": "Material Name",
          "amount": 0.0,
          "unit": "kg",
          "emission_factor": 0.0,
          "note": "Source: Ecoinvent 3.9 — https://ecoinvent.org/database/"
        }}
      ],
      "energy": [
        {{
          "type": "Energy Type",
          "usage": 0.0,
          "unit": "kWh",
          "emission_factor": 0.499,
          "note": "Source: TGO Thailand Grid 2023 — https://www.tgo.or.th"
        }}
      ],
      "transport": [
        {{
          "method": "Transport Mode",
          "distance": 0.0,
          "unit": "km",
          "emission_factor": 0.0,
          "note": "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"
        }}
      ],
      "total_estimated_co2": 0.0,
      "optimization_score": 0,
      "recommendations": [
        "Specific actionable recommendation 1 with quantified impact",
        "Specific actionable recommendation 2 with quantified impact"
      ],
      "summary": "Concise 2-3 sentence executive summary of findings"
    }}

    Document text:
    {content_text}
    """
    try:
        response = client.chat.completions.create(
            model="openrouter/owl-alpha",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"API Error: {e}")


def lookup_emission_factor(material_name: str) -> "EfResult | None":
    """Look up emission factor via Google Search or fallback database."""
    from app.search import search_emission_factor
    return search_emission_factor(material_name)


def save_audit_to_memory(data: dict) -> None:
    """Store completed audit in vector store for future reference."""
    try:
        materials = [m["name"] for m in data.get("materials", [])]
        store_audit(
            project_name=data.get("project_info", {}).get("name", "Unknown"),
            summary=data.get("summary", ""),
            total_co2=data.get("total_estimated_co2", 0),
            materials=materials,
        )
    except Exception as e:
        logger.error(f"Failed to store audit: {e}")


def find_past_audits(materials: list[str]) -> list[dict]:
    """Find similar past audits for reference."""
    try:
        return find_similar_audits(materials)
    except Exception as e:
        logger.error(f"Failed to search past audits: {e}")
        return []
