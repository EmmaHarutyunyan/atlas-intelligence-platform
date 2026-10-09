"""Atlas Intelligence Platform project configuration package.

Importing the Celery app here ensures it is loaded when Django starts, so
that `@shared_task` decorated tasks registered anywhere in the codebase are
picked up automatically.
"""

from config.celery import app as celery_app

__all__ = ("celery_app",)
