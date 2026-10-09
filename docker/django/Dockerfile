# syntax=docker/dockerfile:1

# ---- Base image ------------------------------------------------------------
FROM python:3.13-slim AS base

# Prevent Python from writing .pyc files & buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System dependencies required by psycopg (Postgres), Pillow, Playwright,
# and PostgreSQL health checks.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        postgresql-client \
        curl \
        gnupg \
        chromium \
        chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# ---- Dependency layer -------------------------------------------------------
FROM base AS dependencies

ARG REQUIREMENTS_FILE=requirements/development.txt

COPY requirements/ requirements/

RUN pip install -r ${REQUIREMENTS_FILE}

# Playwright browser binaries
RUN playwright install chromium

# ---- Final application image ------------------------------------------------
FROM dependencies AS app

COPY . .

COPY docker/django/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]