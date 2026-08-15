"""
Django middleware that calls the rate limiter service and either lets
the request through or blocks it with a 429 response.

Port of rate-limiter-service/src/middleware/rateLimiter.ts.

In the original repo, the rate limiter was its own microservice and a
separate "dummy-api-service" called POST /check over HTTP before
handling a request. Here everything lives in one Django project, so
this middleware calls check_rate_limit() directly (no network hop) -
functionally identical, just skipping the HTTP round-trip. If you want
the true microservice split, point this middleware at the /check view
over HTTP instead (see the class docstring below for a drop-in swap).
"""
import logging

from django.http import JsonResponse

from . import metrics
from .config import Plan
from .services import check_rate_limit

logger = logging.getLogger("ratelimiter")

# Routes that must never be rate limited: the health check, the /check
# endpoint itself (that IS the rate limiter), the metrics endpoint, and
# Django admin. Equivalent to registering checkRouter before the
# rate-limiting middleware in the original app.ts.
EXCLUDED_PATHS = {"/health", "/check", "/metrics"}
EXCLUDED_PREFIXES = ("/admin", "/static")


class RateLimiterMiddleware:
    """
    New-style Django middleware (get_response factory pattern).

    To swap this for a *real* microservice call to a separately deployed
    rate-limiter-service, replace the check_rate_limit(...) call below
    with an HTTP POST to RATE_LIMITER_URL + "/check" carrying the same
    {userId, ip, route, plan} JSON body, exactly like
    dummy-api-service/src/rateLimitClient.ts does.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._is_excluded(request.path):
            return self.get_response(request)

        # 1. Extract identity from the request.
        # In a real app, userId would come from a decoded JWT/session.
        # Here (like the original demo) we read it straight from headers.
        user_id = request.headers.get("X-User-Id", "anonymous")
        plan = (request.headers.get("X-User-Plan") or Plan.FREE).upper()
        if plan not in Plan.ALL:
            plan = Plan.FREE
        ip = self._get_client_ip(request)
        route = request.path

        metrics.increment("requests_total")

        # 2. Call the core service.
        result = check_rate_limit(user_id=user_id, ip=ip, route=route, plan=plan)

        # 3. Allow or block.
        if result["allowed"]:
            metrics.increment("requests_allowed")
            response = self.get_response(request)
        else:
            metrics.increment("requests_blocked")
            logger.warning("Request blocked by rate limiter: user_id=%s route=%s plan=%s", user_id, route, plan)
            response = JsonResponse(
                {
                    "success": False,
                    "message": "Too many requests",
                    "reason": result["reason"],
                    "retryAfter": result["reset_after"],
                },
                status=429,
            )
            response["Retry-After"] = str(result["reset_after"])

        # 4. Set rate limit headers on the response either way, so the
        # client always knows exactly where it stands.
        response["X-RateLimit-Limit"] = str(result["limit"])
        response["X-RateLimit-Remaining"] = str(result["remaining"])
        response["X-RateLimit-Reset"] = str(result["reset_after"])
        return response

    @staticmethod
    def _is_excluded(path: str) -> bool:
        if path in EXCLUDED_PATHS:
            return True
        return path.startswith(EXCLUDED_PREFIXES)

    @staticmethod
    def _get_client_ip(request) -> str:
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
