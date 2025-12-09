"""
Authentication utilities for serverless APIs.
- Password hashing via bcrypt
- JWT creation/verification for sessions
"""
import os
import bcrypt
import jwt
import datetime
from typing import Optional, Dict

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALG = "HS256"
JWT_TTL_DAYS = 30
ACTION_TTL_MINUTES = 15


def _require_secret():
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured")


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password is required")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_token(user: Dict, plan: Optional[Dict] = None) -> str:
    _require_secret()
    now = datetime.datetime.utcnow()
    plan_data = plan or {}
    payload = {
        "sub": str(user.get("_id")),
        "email": user.get("email"),
        "plan": plan_data.get("plan") or user.get("plan", "free"),
        "plan_status": plan_data.get("plan_status") or plan_data.get("status") or user.get("plan_status", "inactive"),
        "plan_expires_at": plan_data.get("plan_expires_at") or plan_data.get("expires_at") or user.get("plan_expires_at"),
        "exp": now + datetime.timedelta(days=JWT_TTL_DAYS),
        "iat": now,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def create_action_token(email: str, purpose: str, ttl_minutes: int = ACTION_TTL_MINUTES, extra: Optional[Dict] = None) -> str:
    """Create a short-lived JWT for one-time actions (e.g., upgrade link)."""
    _require_secret()
    now = datetime.datetime.utcnow()
    payload = {
        "sub": email.strip().lower(),
        "email": email.strip().lower(),
        "purpose": purpose,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=ttl_minutes),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def verify_action_token(token: str, purpose: str) -> Optional[Dict]:
    """Validate a purpose-bound JWT; returns payload if valid/purpose matches."""
    if not token or not JWT_SECRET:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        if payload.get("purpose") != purpose:
            return None
        return payload
    except Exception:
        return None


def verify_token(token: str) -> Optional[Dict]:
    if not token:
        return None
    if not JWT_SECRET:
        return None
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except Exception:
        return None


def get_bearer_token(headers) -> Optional[str]:
    auth = None
    if hasattr(headers, "get"):
        auth = headers.get("Authorization") or headers.get("authorization")
    elif isinstance(headers, dict):
        auth = headers.get("Authorization") or headers.get("authorization")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None
