"""
Demo "consumer" endpoints - stand-ins for a real app's /login, /posts,
and /profile routes. Every request to these goes through
RateLimiterMiddleware first, exactly like every request to
dummy-api-service went through the rate-limiter-service's /check call
in the original repo.

Try it:
    curl -i -X POST http://localhost:8000/login \\
        -H "X-User-Id: user1" -H "X-User-Plan: FREE"
    # repeat 6+ times within 60s -> 429 Too Many Requests
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    return JsonResponse({"success": True, "message": "Login successful (demo)"})


@require_http_methods(["GET"])
def posts_view(request):
    return JsonResponse(
        {"success": True, "posts": [{"id": 1, "title": "Hello world"}, {"id": 2, "title": "Second post"}]}
    )


@require_http_methods(["GET"])
def profile_view(request):
    return JsonResponse({"success": True, "profile": {"name": "Demo User", "plan": "FREE"}})
