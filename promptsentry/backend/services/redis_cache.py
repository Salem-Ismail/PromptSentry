"""
redis rate limiting

per-api-key counter in a 60s window. redis is better than postgres for this.
"""

import os

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
RATE_LIMIT_WINDOW_SECONDS = 60

redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def check_rate_limit(api_key: str) -> tuple[bool, int]:
    """
    bump the counter for this key. returns (allowed, current_count).
    """
    # each key gets its own kv pair like rate:apikey1 -> 2
    # next hit from that key is 3, a different key starts at 1
    redis_key = f"rate:{api_key}"

    count = redis_client.incr(redis_key)

    # first hit in the window, start the ttl
    if count == 1:
        redis_client.expire(redis_key, RATE_LIMIT_WINDOW_SECONDS)

    allowed = count <= RATE_LIMIT_PER_MINUTE
    return allowed, count
