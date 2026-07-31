import os
import time
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from detection.llm_judge import judge_prompt
from detection.rule_engine import check_prompt
from services.audit import extract_prompt, extract_response, write_request_log
from services.pii import rebuild_body_with_redacted_prompt, redact_text

router = APIRouter()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def _ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


@router.post("/v1/chat/completions")
async def chat_completions(request: Request) -> Response:
    req_start = time.perf_counter()

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
    t0 = time.perf_counter()
    prompt_text = extract_prompt(body)
    result = check_prompt(prompt_text)
    layer1_ms = _ms(t0)

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
        total_ms = _ms(req_start)
        print(
            f"[latency] BLOCKED layer=1 reason={result['threat_type']} "
            f"layer1={layer1_ms}ms total={total_ms}ms"
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
    t0 = time.perf_counter()
    redacted_prompt, pii_types = redact_text(prompt_text)
    forward_body = rebuild_body_with_redacted_prompt(body, redacted_prompt)
    pii_ms = _ms(t0)


    # layer 2: llm judge on scrubbed prompt only (never raw pii)
    t0 = time.perf_counter()
    judge = await judge_prompt(redacted_prompt)
    layer2_ms = _ms(t0)

    if judge["blocked"]:
        request_id = str(uuid.uuid4())
        write_request_log(
            prompt=redacted_prompt,
            response=None,
            ip_address=client_ip,
            latency_ms=layer2_ms,
            flagged=True,
            threat_type=judge["threat_type"],
            layer=2,
            user_id=user_id,
        )
        total_ms = _ms(req_start)
        print(
            f"[latency] BLOCKED layer=2 reason={judge['reason']} "
            f"confidence={judge['confidence']} "
            f"layer1={layer1_ms}ms pii={pii_ms}ms layer2={layer2_ms}ms "
            f"total={total_ms}ms"
        )
        return JSONResponse(
            status_code=400,
            content={
                "error": "request_blocked",
                "reason": judge["threat_type"],
                "layer": 2,
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "confidence": judge["confidence"],
            },
        )

    t0 = time.perf_counter()
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
    openai_ms = _ms(t0)

    # log the scrubbed prompt only
    response_text = extract_response(upstream.content)

    write_request_log(
        prompt=redacted_prompt,
        response=response_text,
        ip_address=client_ip,
        latency_ms=openai_ms,  # what we store in postgres = openai round trip
        flagged=False,
        user_id=user_id,
    )

    total_ms = _ms(req_start)
    pii_note = ",".join(pii_types) if pii_types else "none"
    print(
        f"[latency] ALLOWED "
        f"layer1={layer1_ms}ms pii={pii_ms}ms layer2={layer2_ms}ms "
        f"openai={openai_ms}ms total={total_ms}ms pii_types={pii_note}"
    )

    # TODO: maybe scrub the response for pii later
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )
