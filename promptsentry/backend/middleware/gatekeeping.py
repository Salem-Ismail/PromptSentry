"""
gatekeeping middleware

runs before most routes:
1. check api key -> 401 if bad
2. rate limit via redis -> 429 if over the limit
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from services.audit import write_request_log
from services.auth import extract_bearer_token, get_valid_api_keys, user_id_from_api_key
from services.redis_cache import RATE_LIMIT_PER_MINUTE, check_rate_limit

# health/docs dont need a key
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class GatekeepingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # who is this
        token = extract_bearer_token(request.headers.get("Authorization"))
        valid_keys = get_valid_api_keys()

        if not token or token not in valid_keys:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "unauthorized",
                    "detail": "Invalid or missing API key. Use: Authorization: Bearer <key>",
                },
            )

        # hashed so we dont dump raw keys into postgres
        request.state.user_id = user_id_from_api_key(token)

        # too many requests?
        allowed, count = check_rate_limit(token)
        if not allowed:
            client_ip = request.client.host if request.client else None
            write_request_log(
                prompt="[rate limited - request not forwarded]",
                response=None,
                ip_address=client_ip,
                latency_ms=0,
                flagged=True,
                threat_type="rate_limit",
                user_id=request.state.user_id,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "too_many_requests",
                    "detail": f"Rate limit exceeded ({RATE_LIMIT_PER_MINUTE} requests per minute).",
                    "count": count,
                },
            )

        return await call_next(request)
