"""
Single shared Redis connection for the whole project.
Port of rate-limiter-service/src/redis/client.ts
"""
import logging

import redis
from django.conf import settings

logger = logging.getLogger("ratelimiter")

redis_client = redis.Redis.from_url(
    settings.RATE_LIMITER["REDIS_URL"],
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
    # redis-py retries the *connection*, not the command, but this keeps
    # startup resilient the same way the ioredis retryStrategy did.
    retry_on_timeout=True,
    health_check_interval=30,
)

try:
    redis_client.ping()
    logger.info("Redis connected successfully")
except redis.RedisError as exc:
    # Don't crash at import time - the service layer's failover mode
    # (open/closed) decides what happens when Redis is actually needed.
    logger.warning("Redis not reachable at startup: %s", exc)
