"""
Standalone "microservice" endpoints for the rate limiter itself.
Port of rate-limiter-service/src/routes/check.ts + app.ts's /health route.

These are excluded from rate limiting (see middleware.py) since /check
IS the rate limiter - it can't rate limit itself.
"""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from . import metrics
from .config import Plan
from .services import check_rate_limit


def health(request):
    return JsonResponse({"status": "ok", "service": "rate-limiter-service"})


@csrf_exempt
@require_http_methods(["POST"])
def check(request):
    """
    POST /check
    Other backend services call this to ask: "is this user allowed to
    make a request right now?" This is what makes the rate limiter a
    standalone service instead of just an in-process middleware.

    Body: {"userId": "...", "ip": "...", "route": "...", "plan": "FREE"}
    """
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)

    user_id = body.get("userId")
    ip = body.get("ip")
    route = body.get("route")
    plan = body.get("plan")
    normalized_plan = plan.upper() if isinstance(plan, str) else plan

    # Basic validation
    if not all([user_id, ip, route, plan]):
        return JsonResponse(
            {"success": False, "message": "Missing required fields: userId, ip, route, plan"},
            status=400,
        )

    # Validate plan value
    if normalized_plan not in Plan.ALL:
        return JsonResponse(
            {"success": False, "message": f"Invalid plan. Must be one of: {', '.join(Plan.ALL)}"},
            status=400,
        )

    result = check_rate_limit(user_id=user_id, ip=ip, route=route, plan=normalized_plan)

    return JsonResponse(
        {
            "success": result["allowed"],
            "allowed": result["allowed"],
            "limit": result["limit"],
            "remaining": result["remaining"],
            "resetAfter": result["reset_after"],
            "reason": result["reason"],
        },
        status=200 if result["allowed"] else 429,
    )


def metrics_view(request):
    """GET /metrics - snapshot of the in-memory counters."""
    return JsonResponse(metrics.get_metrics())
