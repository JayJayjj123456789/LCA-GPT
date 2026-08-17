"""LCA-GPT — Multi-user authentication (PostgreSQL-backed sessions).

Passwords are hashed with PBKDF2-HMAC-SHA256 (stdlib only).
Sessions are random bearer tokens stored in the `sessions` table so they
survive server restarts and redeploys.
"""

import hashlib
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException

from app.vector_store import _pg_conn, _pg_enabled, _pg_ensure

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PBKDF2_ITERATIONS = 200_000
_SESSION_TTL_DAYS = 30


# ── Password hashing ─────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, _PBKDF2_ITERATIONS
    )
    return f"pbkdf2${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt_hex, hash_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iters)
        )
        return secrets.compare_digest(digest.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


# ── Sessions ─────────────────────────────────────────────────────────────────

def create_session(email: str) -> str:
    _pg_ensure()
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=_SESSION_TTL_DAYS)
    with _pg_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (token, user_email, expires_at) VALUES (%s, %s, %s)",
            (token, email, expires),
        )
    return token


def get_session_email(token: str) -> str | None:
    """Return the user email for a valid, unexpired session token."""
    _pg_ensure()
    try:
        with _pg_conn() as conn:
            row = conn.execute(
                "SELECT user_email, expires_at FROM sessions WHERE token = %s",
                (token,),
            ).fetchone()
        if not row:
            return None
        email, expires = row
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            return None
        return email
    except Exception as e:
        logger.error(f"Session lookup failed: {e}")
        return None


def delete_session(token: str) -> None:
    try:
        _pg_ensure()
        with _pg_conn() as conn:
            conn.execute("DELETE FROM sessions WHERE token = %s", (token,))
    except Exception as e:
        logger.error(f"Session delete failed: {e}")


# ── User records ─────────────────────────────────────────────────────────────

def find_user(email: str) -> dict | None:
    _pg_ensure()
    with _pg_conn() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash FROM users WHERE email = %s",
            (email,),
        ).fetchone()
    if not row:
        return None
    return {"id": row[0], "email": row[1], "password_hash": row[2]}


def create_user(email: str, password: str) -> None:
    """Create a user; the first user claims any legacy (owner-less) audits."""
    _pg_ensure()
    with _pg_conn() as conn:
        conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
            (email, hash_password(password)),
        )
        # First user in the system owns the pre-existing legacy audits
        count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
        if count == 1:
            claimed = conn.execute(
                "UPDATE audits SET owner_id = %s WHERE owner_id IS NULL RETURNING id",
                (email,),
            ).fetchall()
            if claimed:
                logger.info(f"First user {email} claimed {len(claimed)} legacy audit(s)")
        conn.commit()


def count_users() -> int:
    _pg_ensure()
    with _pg_conn() as conn:
        return conn.execute("SELECT count(*) FROM users").fetchone()[0]


def validate_registration(email: str, password: str) -> str | None:
    """Return an error message, or None when the input is acceptable."""
    if not email or not _EMAIL_RE.match(email):
        return "Please enter a valid email address."
    if not password or len(password) < 6:
        return "Password must be at least 6 characters."
    return None


# ── FastAPI dependency ───────────────────────────────────────────────────────

def require_user(authorization: str = Header(None)) -> str:
    """Return the authenticated user's email or raise HTTP 401."""
    if not _pg_enabled():
        raise HTTPException(503, "Database not configured")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Not authenticated")
    token = authorization.split(" ", 1)[1].strip()
    email = get_session_email(token)
    if not email:
        raise HTTPException(401, "Invalid or expired session")
    return email
