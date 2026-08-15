"""
The brain of the whole system. Takes a request, runs the sliding-window
algorithm atomically in Redis, and returns allowed/blocked.

Port of rate-limiter-service/src/services/rateLimiterService.ts + luaScripts.ts.

We use redis-py's `Script` object (`redis_client.register_script`) instead
of manually managing SCRIPT LOAD / EVALSHA / SHA caching by hand - it does
the same EVALSHA-first-then-fallback-to-EVAL-on-NOSCRIPT dance internally,
so we get the same atomicity and performance without re-implementing it.
"""
import logging
import time
from pathlib import Path

from django.conf import settings

from . import metrics
from .config import Plan, get_plan_config, get_route_config
from .redis_client import redis_client

logger = logging.getLogger("ratelimiter")

_LUA_PATH = Path(__file__).resolve().parent / "lua" / "sliding_window.lua"
_SLIDING_WINDOW_SCRIPT_SRC = _LUA_PATH.read_text(encoding="utf-8")

# This registers the script's SHA the first time it's actually executed,
# and transparently retries with EVAL if Redis ever evicts it (NOSCRIPT).
sliding_window_script = redis_client.register_script(_SLIDING_WINDOW_SCRIPT_SRC)


def check_rate_limit(user_id: str, ip: str, route: str, plan: str) -> dict:
    """
    Figure out which limit applies (route config wins over plan config),
    run the sliding-window Lua script atomically, and return a result dict:

        {allowed, limit, remaining, reset_after, reason}
    """
    route_config = get_route_config(route)
    plan_config = get_plan_config(plan)

    limit = route_config["limit"] if route_config else plan_config["limit"]
    window_secs = route_config["window_secs"] if route_config else plan_config["window_secs"]

    # key format --> ratelimit:userId:ip:route
    # each user + ip + route combination gets its own ZSET in Redis
    redis_key = f"ratelimit:{user_id}:{ip}:{route}"

    now_ms = int(time.time() * 1000)
    window_ms = window_secs * 1000

    try:
        allowed_flag, remaining_raw = sliding_window_script(
            keys=[redis_key],
            args=[now_ms, window_ms, limit],
        )
        allowed = int(allowed_flag) == 1
        remaining = int(remaining_raw)

        result = {
            "allowed": allowed,
            "limit": limit,
            "remaining": remaining if allowed else 0,
            "reset_after": window_secs,
            "reason": None if allowed else "Rate limit exceeded",
        }

        logger.info(
            "rate_limit_check user_id=%s route=%s plan=%s allowed=%s remaining=%s limit=%s",
            user_id, route, plan, allowed, result["remaining"], limit,
        )
        return result

    except Exception:
        # Redis failed - apply the configured failover strategy.
        logger.exception("Redis error during rate limit check (user_id=%s)", user_id)
        metrics.increment("redis_errors")

        failover_mode = settings.RATE_LIMITER["FAILOVER_MODE"]

        if failover_mode == "open":
            # fail-open: Redis is down, let the request through.
            # Availability > strict enforcement.
            logger.warning("Failing open - allowing request due to Redis unavailability")
            metrics.increment("failover_open")
            return {
                "allowed": True,
                "limit": limit,
                "remaining": -1,
                "reset_after": window_secs,
                "reason": "Rate limiter unavailable - failing open",
            }
        else:
            # fail-closed: Redis is down, block the request.
            # Strict enforcement > availability.
            logger.warning("Failing closed - blocking request due to Redis unavailability")
            metrics.increment("failover_closed")
            return {
                "allowed": False,
                "limit": limit,
                "remaining": 0,
                "reset_after": window_secs,
                "reason": "Rate limiter unavailable - failing closed",
            }
