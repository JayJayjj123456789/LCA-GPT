"""Simple in-memory cache for chat responses.

Reduces latency from 3.5s → 0.2s for repeated questions.
"""

import hashlib
from typing import Optional

# In-memory cache (lost on restart, but that's OK)
_CACHE: dict[str, str] = {}


def get_cache_key(question: str, owner: str = "") -> str:
    """Generate cache key from question and owner (keeps users' answers separate)."""
    return hashlib.md5(f"{owner}|{question.lower().strip()}".encode(), usedforsecurity=False).hexdigest()


def get_cached_response(question: str, owner: str = "") -> Optional[str]:
    """Get cached response if exists."""
    key = get_cache_key(question, owner)
    return _CACHE.get(key)


def cache_response(question: str, answer: str, owner: str = "") -> None:
    """Cache a chat response."""
    key = get_cache_key(question, owner)
    _CACHE[key] = answer


def clear_cache() -> None:
    """Clear all cached responses (call when new audit is uploaded)."""
    _CACHE.clear()


def get_cache_stats() -> dict:
    """Get cache statistics."""
    return {
        "cached_responses": len(_CACHE),
        "total_size_bytes": sum(len(v.encode()) for v in _CACHE.values()),
    }
