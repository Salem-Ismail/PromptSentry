import os
import time
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from detection.rule_engine import check_prompt
from services.audit import extract_prompt, extract_response, write_request_log
from services.pii import rebuild_body_with_redacted_prompt, redact_text

router = APIRouter()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


@router.post("/v1/chat/completions")
async def chat_completions(request: Request) -> Response:
    # need our upstream key or nothing works
    if not OPENAI_API_KEY:
        return Response(
            content='{"error":"OPENAI_API_KEY is not configured"}',
            status_code=500,
            media_type="application/json",
        )

    body = await request.body()

    client_ip = request.client.host if request.client else None
    # gatekeeping middleware sets this from the hashed api key
    user_id = getattr(request.state, "user_id", None)

    # layer 1: keyword check on the original prompt
    prompt_text = extract_prompt(body)
    result = check_prompt(prompt_text)

    if result["blocked"]:
        request_id = str(uuid.uuid4())
        write_request_log(
            prompt=prompt_text,
            response=None,
            ip_address=client_ip,
            latency_ms=0,
            flagged=True,
            threat_type=result["threat_type"],
            layer=1,
            user_id=user_id,
        )
        return JSONResponse(
            status_code=400,
            content={
                "error": "request_blocked",
                "reason": result["threat_type"],
                "layer": 1,
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "confidence": None,
            },
        )

    # pii: redact then rebuild so openai never sees the raw phone/email
    redacted_prompt, _pii_types = redact_text(prompt_text)
    forward_body = rebuild_body_with_redacted_prompt(body, redacted_prompt)

    started = time.perf_counter()

    async with httpx.AsyncClient() as client:
        upstream = await client.post(
            f"{OPENAI_BASE_URL}/v1/chat/completions",
            content=forward_body,
            headers={
                # our openai key, not the client's promptsentry key
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=60.0,  # dont hang forever if openai is down
        )

    latency_ms = int((time.perf_counter() - started) * 1000)

    # log the scrubbed prompt only
    response_text = extract_response(upstream.content)

    write_request_log(
        prompt=redacted_prompt,
        response=response_text,
        ip_address=client_ip,
        latency_ms=latency_ms,
        flagged=False,
        user_id=user_id,
    )

    # TODO: maybe scrub the response for pii later
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )
