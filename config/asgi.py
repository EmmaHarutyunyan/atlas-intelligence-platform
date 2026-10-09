"""ASGI entrypoint.

Not used for serving traffic yet (Gunicorn/WSGI handles that), but kept ready
for a future milestone that adds websocket-based live notifications via
Django Channels.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

application = get_asgi_application()
