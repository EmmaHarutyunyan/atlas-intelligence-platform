"""Celery application factory for Atlas Intelligence Platform.

Celery Beat schedules (periodic tasks) are configured via
`django-celery-beat`'s database-backed scheduler rather than a static
`beat_schedule` dict, so recurring scraping jobs can be created/edited from
the Django admin or API without a redeploy. Schedules are created programmatically by the core scheduling service.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("dataforge")

# Read all celery-related config from Django settings, using the `CELERY_`
# prefix as the namespace (e.g. CELERY_BROKER_URL).
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover `tasks.py` modules in every installed app.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:
    """Diagnostic task used to verify the Celery worker is wired up correctly."""
    print(f"Request: {self.request!r}")
