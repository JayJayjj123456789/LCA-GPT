import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "poolside/laguna-s-2.1:free")

# Secret key protecting the database viewer page (/db-view). When unset,
# the viewer and its API are disabled (404).
SECRET_DATA_KEY = os.getenv("SECRET_DATA_KEY", "")

# ─── Active LLM provider ──────────────────────────────────────────────────────
# Groq is used when GROQ_API_KEY is present; falls back to OpenRouter otherwise.
_GROQ_API_KEY = os.getenv("GROQ_API_KEY")
_GROQ_MODEL   = os.getenv("GROQ_MODEL", "groq/compound")
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
