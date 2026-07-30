"""
audit logging helpers

we only parse json for the db. the proxy still forwards its own body bytes (or the rebuilt redacted ones).
"""

import json
from typing import Any

from db import SessionLocal
from models.request_log import RequestLog


def extract_prompt(body: bytes) -> str:
    """
    grab the latest user message from an openai-style chat body
    """
    try:
        data: dict[str, Any] = json.loads(body)
        messages = data.get("messages", [])
        if not isinstance(messages, list):
            return _fallback_text(body)

        user_parts: list[str] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            if message.get("role") != "user":
                continue
            content = message.get("content")
            if isinstance(content, str):
                user_parts.append(content)

        if user_parts:
            return user_parts[-1]

    except (json.JSONDecodeError, TypeError, KeyError):
        pass

    return _fallback_text(body)


def extract_response(content: bytes) -> str | None:
    """pull assistant content out of a chat completion response"""
    try:
        data: dict[str, Any] = json.loads(content)
        choices = data.get("choices", [])
        if not choices:
            return None
        message = choices[0].get("message", {})
        reply = message.get("content")
        return reply if isinstance(reply, str) else None
    except (json.JSONDecodeError, TypeError, KeyError, IndexError):
        return None


def _fallback_text(body: bytes) -> str:
    # if json is broken just stash something so we still have a row
    return body.decode("utf-8", errors="replace")[:5000]


def write_request_log(
    *,
    prompt: str,
    response: str | None,
    ip_address: str | None,
    latency_ms: int,
    flagged: bool = False,
    threat_type: str | None = None,
    layer: int | None = None,
    user_id: str | None = None,
) -> None:
    """insert one row into request_logs"""
    db = SessionLocal()
    try:
        row = RequestLog(
            prompt=prompt,
            response=response,
            ip_address=ip_address,
            latency_ms=latency_ms,
            flagged=flagged,
            threat_type=threat_type,
            layer=layer,
            user_id=user_id,
        )
        db.add(row)
        db.commit()
    finally:
        db.close()
