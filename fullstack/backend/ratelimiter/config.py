"""
Plan-based and route-based rate limit configuration.
Direct port of rate-limiter-service/src/config/index.ts
"""


class Plan:
    """String enum of subscription plans (mirrors the TS `Plan` enum)."""
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

    ALL = (FREE, PRO, ENTERPRISE)


# Default limits per plan - applies to all routes unless a route-specific
# config overrides it.
PLAN_CONFIGS = {
    Plan.FREE: {"limit": 100, "window_secs": 900},        # 100 req / 15 min
    Plan.PRO: {"limit": 1000, "window_secs": 900},         # 1000 req / 15 min
    Plan.ENTERPRISE: {"limit": 10000, "window_secs": 900},  # 10000 req / 15 min
}

# Route-specific limits override plan limits.
# /login is stricter - brute force attacks happen there.
# /posts is relaxed - it's just reading data.
ROUTE_CONFIGS = {
    "/login": {"limit": 5, "window_secs": 60},
    "/posts": {"limit": 200, "window_secs": 60},
    "/profile": {"limit": 50, "window_secs": 60},
}


def get_plan_config(plan: str) -> dict:
    """Given a plan, return its config. Falls back to FREE if unknown."""
    return PLAN_CONFIGS.get(plan, PLAN_CONFIGS[Plan.FREE])


def get_route_config(route: str) -> dict | None:
    """Given a route, return its specific config if one exists, else None."""
    return ROUTE_CONFIGS.get(route)
