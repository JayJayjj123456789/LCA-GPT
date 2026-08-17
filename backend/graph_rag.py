"""LCA-GPT — Graph RAG Chat System"""

import logging

import openai
from dotenv import load_dotenv

from app.config import ACTIVE_API_KEY, ACTIVE_MODEL, ACTIVE_BASE_URL

load_dotenv()

logger = logging.getLogger(__name__)

_client = openai.OpenAI(
    base_url=ACTIVE_BASE_URL,
    api_key=ACTIVE_API_KEY,
)


def _build_context_from_memory(owner: str | None = None) -> str:
    from app.vector_store import get_full_audits
    audits = get_full_audits(owner)
    if not audits:
        return ""
    parts = []
    for d in audits[-3:]:  # last 3 audits
        info = d.get("project_info", {})
        parts.append(f"Project: {info.get('name')} | Supplier: {info.get('supplier')}")
        parts.append(f"Total CO2: {d.get('total_estimated_co2')} kgCO2e | Score: {d.get('optimization_score')}/100")
        for m in d.get("materials", []):
            parts.append(f"  Material: {m['name']} {m['amount']} {m['unit']} EF={m['emission_factor']}")
        for e in d.get("energy", []):
            parts.append(f"  Energy: {e['type']} {e['usage']} {e['unit']} EF={e['emission_factor']}")
        for t in d.get("transport", []):
            parts.append(f"  Transport: {t['method']} {t['distance']} {t['unit']} EF={t['emission_factor']}")
        parts.append(f"Summary: {d.get('summary', '')}")
        for r in d.get("recommendations", []):
            parts.append(f"  Recommendation: {r}")
        parts.append("")
    return "\n".join(parts)


def ask_graph(question: str, owner: str | None = None) -> str:
    """Answer question from the user's stored audits (per-user context).

    FIX 1: Response caching for performance (3.5s → 0.2s for cached).
    FIX 2: Context and cache are scoped per user (multi-user).
    """
    # Check cache first
    from backend.cache import get_cached_response, cache_response
    cached = get_cached_response(question, owner or "")
    if cached:
        logger.info(f"Cache HIT for question: {question[:50]}...")
        return cached

    logger.info(f"Cache MISS for question: {question[:50]}...")
    context = _build_context_from_memory(owner)

    if not context:
        context = "ไม่มีข้อมูล audit ในระบบขณะนี้"

    system_prompt = """You are an expert Life Cycle Assessment (LCA) consultant and carbon footprint analyst.

⚠️ CRITICAL RULES — READ CAREFULLY:
1. Answer questions ONLY using the audit data provided below.
2. DO NOT use your general knowledge or make assumptions beyond the data.
3. If the answer is not found in the audit data, respond EXACTLY: "ไม่มีข้อมูลนี้ใน audit ปัจจุบัน" (in Thai) or "This information is not available in the current audit" (in English)
4. DO NOT fabricate numbers, emission factors, materials, or recommendations.
5. Always cite the specific data from the audit when answering (e.g., "จาก audit พบว่า Material X มีปริมาณ 120 pcs")
6. If multiple materials/items match the question, list ALL of them with their values.
7. When comparing items (e.g., "highest", "lowest"), show the comparison explicitly with numbers.

Language Rules:
- If asked in Thai → respond in Thai (ภาษาไทย)
- If asked in English → respond in English
- Use professional terminology appropriate for LCA/sustainability domain
- Be consistent: don't mix Thai and English in the same sentence unless necessary for technical terms

Answer Format:
- For "yes/no" questions with no data → "ไม่มีข้อมูลนี้ใน audit ปัจจุบัน"
- For data questions → cite the exact values from audit
- For comparison questions → show all relevant items with their values
- Keep answers concise (< 200 words) but complete

Be helpful, concise, and professional. Always ground your answer in the provided audit data."""

    try:
        response = _client.chat.completions.create(
            model=ACTIVE_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Audit data:\n{context}\n\nQuestion: {question}"},
            ],
            temperature=0.1,  # OPTIMIZED: Lower temperature for more factual responses
            top_p=0.9,        # ADDED: Nucleus sampling for better quality
            # poolside/laguna-s-2.1:free is a non-reasoning model; 800 tokens is
            # sufficient for concise Q&A answers.
            max_tokens=800,
            frequency_penalty=0.3,  # ADDED: Reduce repetition
        )
        answer = response.choices[0].message.content

        # Reasoning models can return content=None if the token budget is exhausted
        # during the reasoning phase (finish_reason="length"). Guard against it.
        if not answer:
            logger.warning(
                f"Empty LLM content (finish_reason={response.choices[0].finish_reason}); "
                "not caching."
            )
            return "ขออภัยครับ ระบบ AI ไม่สามารถตอบได้ในขณะนี้"

        # Cache the response before returning
        from backend.cache import cache_response
        cache_response(question, answer, owner or "")

        return answer
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return "ขออภัยครับ ระบบ AI ไม่สามารถตอบได้ในขณะนี้"


if __name__ == "__main__":
    test_q = "ในโปรเจกต์มีการใช้วัสดุอะไรบ้าง และปริมาณเท่าไหร่?"
    print(f"❓ คำถามทดสอบ: {test_q}")
    print(ask_graph(test_q))
