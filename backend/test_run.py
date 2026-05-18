"""LCA-GPT — Test Script (Experimental)"""

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test():
    """Test PDF extraction + AI analysis pipeline."""
    try:
        from openai import OpenAI
    except ImportError:
        logger.error("openai package not installed. Run: pip install openai")
        sys.exit(1)

    try:
        from llama_parse import LlamaParse
    except ImportError:
        logger.error("llama-parse not installed. Run: pip install llama-parse")
        sys.exit(1)

    parser = LlamaParse(
        api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
        result_type="markdown",
    )
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    pdf_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_invoice.pdf")

    if not os.path.exists(pdf_path):
        logger.error("PDF not found: %s", pdf_path)
        sys.exit(1)

    logger.info("Reading PDF: %s", pdf_path)
    docs = parser.load_data(pdf_path)
    content = docs[0].text

    response = client.chat.completions.create(
        model="openrouter/owl-alpha",
        messages=[
            {"role": "user", "content": f"Extract JSON from this: {content}"}
        ],
    )
    print("Result:", response.choices[0].message.content)


if __name__ == "__main__":
    test()
