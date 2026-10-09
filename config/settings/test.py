"""Settings used exclusively by the test suite (pytest) and CI.

Uses a real Postgres (matching production) rather than SQLite, so tests
exercise the same constraint/index behavior we rely on in production —
SQLite silently ignores things like certain constraint types.
Password hashing is downgraded to the fastest available hasher purely for
test-suite speed; this setting must never leak into dev/prod.
"""

from config.settings.base import *  # noqa: F403

DEBUG = False

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
