"""Development-only settings.

Optimized for developer feedback loops: verbose errors, permissive hosts,
debug toolbar. Never used in CI or production.
"""

from config.settings.base import *  
from config.settings.base import INSTALLED_APPS, MIDDLEWARE, env

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]

INTERNAL_IPS = ["127.0.0.1"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CORS_ALLOW_ALL_ORIGINS = True

# Surface SQL query counts etc. clearly in the console during development.
LOGGING["loggers"]["django.db.backends"] = {  # noqa: F405
    "handlers": ["console"],
    "level": env.str("SQL_LOG_LEVEL", default="WARNING"),
    "propagate": False,
}
