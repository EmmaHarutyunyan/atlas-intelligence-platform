#!/usr/bin/env bash
# Entrypoint for the Django/Gunicorn container.
#
# Responsibilities:
#   1. Wait for Postgres to accept connections before proceeding.
#   2. Wait for Redis to accept connections before proceeding.
#   3. Run database migrations (idempotent, safe to run on every boot).
#   4. Collect static files in production.
#   5. Hand off to whatever CMD was passed (gunicorn, celery worker, etc.).
set -euo pipefail

wait_for_postgres() {
    echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
    until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" >/dev/null 2>&1; do
        sleep 1
    done
    echo "PostgreSQL is up."
}

wait_for_redis() {
    echo "Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
    until python - <<'PYEOF'
import os
import socket
import sys

host = os.environ["REDIS_HOST"]
port = int(os.environ["REDIS_PORT"])
try:
    with socket.create_connection((host, port), timeout=1):
        sys.exit(0)
except OSError:
    sys.exit(1)
PYEOF
    do
        sleep 1
    done
    echo "Redis is up."
}

wait_for_postgres
wait_for_redis

if [ "${DJANGO_SETTINGS_MODULE}" != "config.settings.test" ]; then
    echo "Applying database migrations..."
    python manage.py migrate --noinput
fi

if [ "${DJANGO_ENV:-development}" = "production" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "Starting: $*"
exec "$@"
