import json
import fitz
import openai
import logging
from app.config import ACTIVE_API_KEY, ACTIVE_MODEL, ACTIVE_BASE_URL
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
        base_url=ACTIVE_BASE_URL,
        api_key=ACTIVE_API_KEY,
    )
    # Chunk long documents: take first + last portion to capture header + line items
    if len(text) <= 12000:
        content_text = text
    else:
        content_text = text[:8000] + "\n...[middle truncated]...\n" + text[-4000:]
    system_prompt = (
        "You are an Expert LCA Sustainability Consultant. Your task is to extract carbon footprint data from ANY supply chain document — invoices, purchase orders, BOMs, receipts, sustainability reports, etc. "
        "CRITICAL: You MUST always return materials/energy/transport with real data. NEVER return empty arrays if there are line items in the document. "
        "INVOICE RULE: For invoices/receipts, map EVERY line item to a material entry. Use Qty × Unit as the amount. "
        "ELECTRONICS/IT RULE: For electronics, use per-unit lifecycle CO2e (not weight-based). Known per-unit EF benchmarks (kgCO2e/unit): "
        "Laptop/Notebook: 300-400 kgCO2e/unit (use 350), "
        "Tablet/iPad: 80-120 kgCO2e/unit (use 100), "
        "Desktop PC: 400-600 kgCO2e/unit (use 500), "
        "Monitor/Display 27-55': 200-350 kgCO2e/unit (use 250), "
        "Large Display 75'+: 400-600 kgCO2e/unit (use 500), "
        "Smartphone: 60-80 kgCO2e/unit (use 70), "
        "Network Switch/AP: 50-100 kgCO2e/unit (use 75), "
        "Server/PDU: 1000-2000 kgCO2e/unit (use 1500), "
        "Printer/MFP: 150-300 kgCO2e/unit (use 200), "
        "Office Chair: 50-80 kgCO2e/unit (use 65), "
        "Sit-Stand Desk: 80-150 kgCO2e/unit (use 120), "
        "Software License (SaaS): estimate 0.1-0.5 kgCO2e/user/year for cloud energy (use 0.2). "
        "For non-electronics materials use mass-based EF in kg. "
        "Methodology: 1. Materials: Ecoinvent 3.9 / product LCA studies 2. Energy: Thailand Grid 0.499 kgCO2e/kWh 3. Transport: GLEC Framework v3. "
        "CRITICAL RULE: Every 'note' field MUST include a REAL, VERIFIABLE source URL. "
        "Format: 'Source: [Database] — https://[url]'. "
        "ONLY use URLs from the following verified working domains: "
        "GHG Protocol: https://ghgprotocol.org/, "
        "IPCC AR6 WG3: https://www.ipcc.ch/report/ar6/wg3/, "
        "Ecoinvent: https://ecoinvent.org/database/, "
        "Climatiq: https://climatiq.io/, "
        "Dell LCA: https://www.dell.com/en-us/dt/corporate/social-impact/advancing-sustainability/climate-action/product-carbon-footprints.htm, "
        "Apple Environmental Report: https://www.apple.com/environment/, "
        "HP Sustainability: https://h20195.www2.hp.com/v2/getpdf.aspx/c08436529.pdf, "
        "TGO Thailand: https://www.tgo.or.th, "
        "IEA Emissions Factors: https://www.iea.org/data-and-statistics/data-product/emissions-factors-2023, "
        "EGAT Thailand: https://www.egat.co.th/, "
        "GLEC Framework: https://www.smartfreightcentre.org/en/glec/, "
        "EPA GHG Hub: https://www.epa.gov/climateleadership/ghg-emission-factors-hub. "
        "NEVER return empty materials/energy/transport if there are line items. Return clean JSON only. No markdown."
    )
    user_prompt = f"""
    Analyze the following supply chain document for a complete Carbon Footprint / LCA audit.

    Document type detection rules:
    - If it contains invoice lines with Qty/Amount → map EVERY line item to a material
    - If it's electronics/IT items → use per-unit lifecycle CO2e (unit = "pcs" or "unit")
    - If it has energy consumption data → fill the energy array
    - If it mentions shipping/delivery/logistics → fill transport array

    MANDATORY: The 'note' field for EVERY item MUST follow this exact format:
    'Source: [Database Name] — https://[real-url-to-source]'

    Required JSON structure:
    {{
      "project_info": {{
        "name": "Project name derived from document (e.g. invoice title or company name)",
        "supplier": "Supplier/vendor company name"
      }},
      "materials": [
        {{
          "name": "Product/Material name from invoice line",
          "amount": 120.0,
          "unit": "pcs",
          "emission_factor": 350.0,
          "note": "Source: HP Product Carbon Footprint — https://h20195.www2.hp.com/v2/getpdf.aspx/c08436529.pdf"
        }}
      ],
      "energy": [
        {{
          "type": "Electricity (estimated operational use)",
          "usage": 0.0,
          "unit": "kWh",
          "emission_factor": 0.499,
          "note": "Source: TGO Thailand Grid 2023 — https://www.tgo.or.th"
        }}
      ],
      "transport": [
        {{
          "method": "Road Freight (estimated delivery)",
          "distance": 0.0,
          "unit": "km",
          "emission_factor": 0.1,
          "note": "Source: GLEC Framework v3 — https://www.smartfreightcentre.org/en/glec/"
        }}
      ],
      "total_estimated_co2": 0.0,
      "optimization_score": 0,
      "recommendations": [
        "Specific actionable recommendation with quantified impact"
      ],
      "summary": "Concise 2-3 sentence executive summary of findings"
    }}

    Rules:
    - EVERY invoice line item → one materials entry (do not skip any)
    - Use the Qty column as 'amount'
    - For software/SaaS licenses: amount = number of users, unit = 'license', EF = 0.2 kgCO2e/license
    - For services with no physical product: still create an entry using estimated resource/energy equivalents
    - Calculate total_estimated_co2 = sum(amount × emission_factor) for all items
    - optimization_score = 0-100 based on sustainability of purchasing choices
    - If transport/shipping info not explicit, estimate based on typical Bangkok delivery

    Document text:
    {content_text}
    """
    try:
        response = client.chat.completions.create(
            model=ACTIVE_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            # poolside/laguna-s-2.1:free is a non-reasoning model; 2000 tokens is
            # sufficient for the full JSON extraction output.
            max_tokens=2000,
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError(
                f"Empty model response (finish_reason={response.choices[0].finish_reason}); "
                "model returned no content."
            )
        # Strip markdown code fences some models wrap around JSON output
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]  # drop opening fence line
            content = content.rsplit("```", 1)[0]  # drop closing fence
            content = content.strip()
        return content
    except Exception as e:
        raise RuntimeError(f"API Error: {e}")



def save_audit_to_memory(data: dict, owner: str | None = None) -> None:
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


def find_past_audits(materials: list[str], owner: str | None = None) -> list[dict]:
    """Find similar past audits for reference."""
    try:
        return find_similar_audits(materials, owner=owner)
    except Exception as e:
        logger.error(f"Failed to search past audits: {e}")
        return []
