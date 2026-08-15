"""
Django settings for ratelimiter_project.

Ported from the original Node.js/TypeScript "Rate-Limiter" microservice.
Same sliding-window algorithm, same Redis + Lua atomicity, same
plan/route config shape - implemented as a Django middleware instead
of an Express middleware.
"""

import os
from pathlib import Path

from corsheaders.defaults import default_headers

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Base configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-secret-key-change-me-in-production",
)


DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"


ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "*",
    ).split(",")
    if host.strip()
]


# ---------------------------------------------------------------------------
# Installed applications
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "corsheaders",

    # Local apps
    "ratelimiter",
    "dummy_api",
]


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # Static files
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # CORS MUST be before CommonMiddleware
    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # Custom rate limiter
    "ratelimiter.middleware.RateLimiterMiddleware",
]


# ---------------------------------------------------------------------------
# URL / WSGI
# ---------------------------------------------------------------------------

ROOT_URLCONF = "ratelimiter_project.urls"

WSGI_APPLICATION = "ratelimiter_project.wsgi.application"


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        )
    },
]


# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage"
        ),
    },
}


# ---------------------------------------------------------------------------
# Django defaults
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ===========================================================================
# RATE LIMITER
# ===========================================================================

RATE_LIMITER = {
    # Production Redis URL comes from Render environment variables.
    #
    # Local development:
    # redis://localhost:6379
    #
    # Production:
    # REDIS_URL configured in Render
    "REDIS_URL": os.environ.get(
        "REDIS_URL",
        "redis://localhost:6379",
    ),

    # Redis unavailable:
    #
    # open   -> allow requests
    # closed -> block requests
    "FAILOVER_MODE": os.environ.get(
        "FAILOVER_MODE",
        "open",
    ),
}


# ===========================================================================
# CORS
# ===========================================================================

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        ",".join(
            [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]
        ),
    ).split(",")
    if origin.strip()
]


# ---------------------------------------------------------------------------
# IMPORTANT:
# Your React frontend sends these custom headers:
#
# X-User-Id
# X-User-Plan
#
# Without these headers Django CORS rejects the browser preflight request.
# ---------------------------------------------------------------------------

CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-user-id",
    "x-user-plan",
]


# ---------------------------------------------------------------------------
# Allow JavaScript to READ rate-limit response headers
# ---------------------------------------------------------------------------

CORS_EXPOSE_HEADERS = [
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
    "X-RateLimit-Reset",
    "Retry-After",
]


# ===========================================================================
# RENDER
# ===========================================================================

RENDER_EXTERNAL_HOSTNAME = os.environ.get(
    "RENDER_EXTERNAL_HOSTNAME"
)

if RENDER_EXTERNAL_HOSTNAME:

    if RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(
            RENDER_EXTERNAL_HOSTNAME
        )

    CSRF_TRUSTED_ORIGINS = [
        f"https://{RENDER_EXTERNAL_HOSTNAME}"
    ]


# ===========================================================================
# LOGGING
# ===========================================================================

LOGGING = {
    "version": 1,

    "disable_existing_loggers": False,

    "formatters": {
        "verbose": {
            "format": (
                "%(asctime)s "
                "[%(levelname)s] "
                "%(name)s: "
                "%(message)s"
            ),
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },

    "root": {
        "handlers": ["console"],
        "level": os.environ.get(
            "LOG_LEVEL",
            "INFO",
        ).upper(),
    },
}
