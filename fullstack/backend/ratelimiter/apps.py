from django.apps import AppConfig


class RatelimiterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ratelimiter"

    def ready(self):
        # Touch the services module on startup so the Lua script gets
        # registered with Redis as soon as Django boots - mirrors
        # loadLuaScripts() being awaited before server.listen() in
        # the original server.ts.
        from . import services  # noqa: F401
