# Atlas Intelligence Platform

Atlas is a Django-based web data-intelligence platform. Give it a public HTTP/HTTPS URL and it validates the destination, chooses an appropriate scraping strategy, extracts structured information, deduplicates records, stores the results in PostgreSQL, and exposes them through the web UI and REST API.

## Features

- Universal public URL scraping (not tied to a single website)
- SSRF protection with DNS/IP validation and redirect validation
- Automatic strategy: BeautifulSoup → Playwright → Selenium when needed
- Explicit BeautifulSoup, Playwright and Selenium strategies
- Generic metadata, headings, links, images, tables, lists and page-content extraction
- JSON-LD extraction for Product, Article, NewsArticle, BlogPosting and other schemas
- Product attributes such as price, currency, availability, rating, reviews, brand, SKU and category when available
- Article attributes such as author and publication date when available
- Repeated-item/listing extraction
- Optional CSS-selector extraction rules
- Pagination limits, record limits, timeouts and request delays
- PostgreSQL deduplication with stable content hashes
- Asynchronous Celery JobRuns with Redis
- Celery Beat hourly/daily/weekly scheduling through django-celery-beat
- Search, filtering, pagination and CSV/XLSX export
- Django authentication and object-level ownership isolation
- JWT-authenticated Django REST Framework API and Swagger/OpenAPI docs
- Optional AI provider abstraction; scraping works without an AI key
- Django Admin support for jobs, runs and records
- Docker Compose services for Django, PostgreSQL, Redis, Celery worker, Celery Beat and Flower

## Architecture

```text
Browser / REST client
        |
        v
     Django
        |
   +----+----------------+
   |                     |
 Web UI / DRF        PostgreSQL
   |
 Celery task queue
   |
  Redis <---- Celery Beat
   |
 Celery worker
   |
 URL validator
   |
 HTTP / BeautifulSoup
   |       |
   |      fallback
   |       v
   |    Playwright
   |       |
   |      fallback
   |       v
   |    Selenium
   |
 Structured extraction -> normalization -> deduplication -> PostgreSQL
```

## Run with Docker

1. Copy `.env.example` to `.env` and set a strong `DJANGO_SECRET_KEY`.
2. Start the stack:

```bash
docker compose up --build
```

3. Open `http://localhost:8000/`.
4. Create an account, create a job, enter a public URL and run it.

The Docker image installs Chromium and Chromium Driver so both browser strategies can operate in the container. PostgreSQL and Redis use persistent named volumes.

Useful commands:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web pytest
docker compose logs -f celery-worker
docker compose logs -f celery-beat
```

## API

- `POST /api/token/`
- `POST /api/token/refresh/`
- `GET/POST /api/jobs/`
- `GET/PATCH/DELETE /api/jobs/{id}/`
- `POST /api/jobs/{id}/run/`
- `GET /api/records/`
- `GET /api/runs/`
- `GET /api/schema/`
- `GET /api/docs/`

API querysets are scoped to the authenticated user.

## Environment variables

See `.env.example` for Django, PostgreSQL, Redis/Celery, OpenAI and optional Sentry settings. Never commit `.env` or API keys.

## Testing

The test suite covers extraction, JSON-LD, SSRF protection and object ownership. Browser/Celery integration tests run in the full Docker/CI environment.

```bash
pytest
```

## Limitations

Atlas intentionally limits pagination and records per job to prevent uncontrolled crawling. Websites protected by authentication, CAPTCHAs, robots/policies that deny access, or heavily interactive workflows may still require site-specific handling. AI extraction is optional and is not required for the normal scraping pipeline.

<img width="2482" height="4752" alt="Image" src="https://github.com/user-attachments/assets/f9accc9a-8f2d-4bdf-9392-834cb7e2e818" />

<img width="2482" height="4752" alt="Image" src="https://github.com/user-attachments/assets/c83f55e9-4e0d-4c23-a42a-6c21829b73e7" />

<img width="2490" height="3258" alt="Image" src="https://github.com/user-attachments/assets/d0a30539-b008-4135-8be0-a6b0a55df735" />

<img width="2490" height="5650" alt="Image" src="https://github.com/user-attachments/assets/06698410-2b7a-41c3-87bd-bf62ffeaf4c2" />
