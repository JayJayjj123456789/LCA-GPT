import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PW = os.getenv("NEO4J_PASSWORD")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "poolside/laguna-s-2.1:free")
APP_ID = os.getenv("APP_ID", "lca-gpt-enterprise")

# ─── Active LLM provider ──────────────────────────────────────────────────────
# Groq is used when GROQ_API_KEY is present; falls back to OpenRouter otherwise.
_GROQ_API_KEY = os.getenv("GROQ_API_KEY")
_GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

if _GROQ_API_KEY:
    ACTIVE_API_KEY  = _GROQ_API_KEY
    ACTIVE_MODEL    = _GROQ_MODEL
    ACTIVE_BASE_URL = _GROQ_BASE_URL
else:
    ACTIVE_API_KEY  = OPENROUTER_API_KEY
    ACTIVE_MODEL    = OPENROUTER_MODEL
    ACTIVE_BASE_URL = _OPENROUTER_BASE_URL
