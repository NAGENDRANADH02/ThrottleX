from django.contrib import admin
from django.urls import path

from ratelimiter import views as rl_views
from dummy_api import views as demo_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- Rate limiter "microservice" endpoints (excluded from limiting) ---
    path("health", rl_views.health, name="health"),
    path("check", rl_views.check, name="check"),
    path("metrics", rl_views.metrics_view, name="metrics"),

    # --- Demo consumer endpoints (protected by RateLimiterMiddleware) ---
    path("login", demo_views.login_view, name="login"),
    path("posts", demo_views.posts_view, name="posts"),
    path("profile", demo_views.profile_view, name="profile"),
]
