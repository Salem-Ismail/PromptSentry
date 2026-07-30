"""
auth helpers for promptsentry api keys (not the openai key)
"""

import hashlib
import os


def get_valid_api_keys() -> set[str]:
    # comma separated list in .env
    raw = os.getenv("PROMPTSENTRY_API_KEYS", "")
    return {key.strip() for key in raw.split(",") if key.strip()}


def extract_bearer_token(authorization: str | None) -> str | None:
    """
    pull the token out of: Authorization: Bearer ps_xxx
    """
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def user_id_from_api_key(api_key: str) -> str:
    # short hash for logs, dont store the raw key
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]
