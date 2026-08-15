"""
Simple in-memory counters tracking what the rate limiter is doing.
Port of rate-limiter-service/src/metrics/index.ts

Note: like the original, these counters live in process memory. If you
run Django behind multiple workers/processes (gunicorn -w N), each
worker has its own counters - fine for a demo, swap for Redis-backed
counters if you need a single source of truth in production.
"""
import threading

_lock = threading.Lock()

_counters = {
    "requests_total": 0,      # every request that came in
    "requests_allowed": 0,    # requests we let through
    "requests_blocked": 0,    # requests we blocked with 429
    "redis_errors": 0,        # times Redis failed on us
    "failover_open": 0,       # times we failed open
    "failover_closed": 0,     # times we failed closed
}


def increment(metric: str) -> None:
    with _lock:
        if metric in _counters:
            _counters[metric] += 1


def get_metrics() -> dict:
    with _lock:
        return dict(_counters)


def reset_metrics() -> None:
    with _lock:
        for key in _counters:
            _counters[key] = 0
