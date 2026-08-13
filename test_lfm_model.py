"""Verification harness for liquid/lfm-2.5-2.6b:free on OpenRouter.

Runs three checks against the LCA-GPT RAG pipeline:
  1. Extraction  — run analyzer on docs/sample_purchase_order.pdf
  2. Hallucination — feed known audit context and ask an out-of-scope question;
                     the model must refuse instead of fabricating.
  3. Rate limiting — fire N sequential requests and report 429 / latency behavior.

Usage:  python test_lfm_model.py
"""
import os
import time

import openai

from app.config import ACTIVE_API_KEY, ACTIVE_MODEL, ACTIVE_BASE_URL

SEP = "=" * 70


def _client() -> openai.OpenAI:
    return openai.OpenAI(
        base_url=ACTIVE_BASE_URL,
        api_key=ACTIVE_API_KEY,
    )


def check_model_config() -> None:
    print(SEP)
    print("MODEL CONFIG")
    print(SEP)
    print(f"ACTIVE_MODEL     = {ACTIVE_MODEL}")
    print(f"ACTIVE_BASE_URL  = {ACTIVE_BASE_URL}")
    assert ACTIVE_MODEL, "ACTIVE_MODEL is not set — check .env (GROQ_MODEL or OPENROUTER_MODEL)"
    assert ACTIVE_API_KEY, "ACTIVE_API_KEY is not set — check .env (GROQ_API_KEY or OPENROUTER_API_KEY)"
    print(f"PASS: active provider configured ({ACTIVE_MODEL})\n")


def check_extraction() -> None:
    print(SEP)
    print("TEST 1 — PDF EXTRACTION (docs/sample_purchase_order.pdf)")
    print(SEP)
    from app.analyzer import extract_text_from_pdf, analyze_enterprise_carbon

    pdf = os.path.join(os.path.dirname(__file__), "docs", "sample_purchase_order.pdf")
    text = extract_text_from_pdf(pdf)
    print(f"Extracted {len(text)} chars from PDF")

    t0 = time.time()
    raw = analyze_enterprise_carbon(text)
    dt = time.time() - t0
    print(f"LLM latency: {dt:.2f}s")
    print(f"Raw output ({len(raw)} chars):\n{raw[:1500]}\n")

    import json
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        data = json.loads(cleaned)
        mats = data.get("materials", [])
        print(f"PASS: valid JSON, {len(mats)} materials, "
              f"total_co2={data.get('total_estimated_co2')}\n")
    except json.JSONDecodeError as e:
        print(f"WARN: output was not clean JSON ({e}). "
              f"Small models sometimes wrap output — see raw above.\n")


CONTEXT = """- Steel Beam [amount: 500, unit: kg, emission_factor: 1.9]
- Aluminum Sheet [amount: 200, unit: kg, emission_factor: 11.5]
- Diesel [usage: 300, unit: L, emission_factor: 2.68]"""


def _ask(client, question: str) -> str:
    system = (
        "Answer ONLY from the audit data provided. "
        "If the answer is not in the data, reply EXACTLY: "
        '"This information is not available in the current audit". '
        "Do not fabricate numbers or items."
    )
    r = client.chat.completions.create(
        model=ACTIVE_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Audit data:\n{CONTEXT}\n\nQuestion: {question}"},
        ],
        temperature=0.1,
        max_tokens=2000,
    )
    content = r.choices[0].message.content
    if not content:
        return f"[EMPTY content, finish_reason={r.choices[0].finish_reason}]"
    return content.strip()


def check_hallucination() -> None:
    print(SEP)
    print("TEST 2 — HALLUCINATION GROUNDING")
    print(SEP)
    client = _client()

    grounded_q = "How much steel is in the audit?"
    ans = _ask(client, grounded_q)
    print(f"Q (in-scope): {grounded_q}\nA: {ans}")
    grounded_ok = "500" in ans
    print(f"{'PASS' if grounded_ok else 'FAIL'}: cites 500 kg steel from data\n")

    oos_q = "What is the emission factor for concrete and how many kg of concrete were used?"
    ans2 = _ask(client, oos_q)
    print(f"Q (out-of-scope): {oos_q}\nA: {ans2}")
    refused = "not available" in ans2.lower()
    print(f"{'PASS' if refused else 'FAIL'}: refuses instead of fabricating concrete data\n")


def check_rate_limit(n: int = 8) -> None:
    print(SEP)
    print(f"TEST 3 — RATE LIMITING ({n} sequential requests)")
    print(SEP)
    client = _client()
    ok = err429 = other = 0
    latencies = []
    for i in range(n):
        t0 = time.time()
        try:
            client.chat.completions.create(
                model=ACTIVE_MODEL,
                messages=[{"role": "user", "content": f"Reply with just the number {i}."}],
                max_tokens=500,
                temperature=0,
            )
            dt = time.time() - t0
            latencies.append(dt)
            ok += 1
            print(f"  req {i+1}: OK ({dt:.2f}s)")
        except openai.RateLimitError as e:
            err429 += 1
            print(f"  req {i+1}: 429 RATE LIMIT — {str(e)[:120]}")
        except Exception as e:
            other += 1
            print(f"  req {i+1}: ERROR — {type(e).__name__}: {str(e)[:120]}")
        time.sleep(0.3)

    print(f"\nSummary: {ok} ok, {err429} rate-limited, {other} other errors")
    if latencies:
        print(f"Avg latency: {sum(latencies)/len(latencies):.2f}s")
    if err429:
        print("NOTE: free tier hit its rate ceiling. This is expected for :free "
              "models under burst load — add retry/backoff or a paid fallback.\n")
    else:
        print("No rate limiting observed in this burst.\n")


if __name__ == "__main__":
    check_model_config()
    check_extraction()
    check_hallucination()
    check_rate_limit()
    print(SEP)
    print("DONE")
    print(SEP)
