# Atlas Intelligence Platform — Architecture

Atlas preserves the existing Django + PostgreSQL + Redis + Celery + Docker architecture and adds a modular scraping pipeline.

## Runtime flow

```text
HTTP request
  -> Django job creation
  -> Celery JobRun
  -> URL/SSRF validation
  -> Automatic / BeautifulSoup / Playwright / Selenium
  -> HTML parsing + JSON-LD extraction
  -> product/article/listing/generic normalization
  -> content hash deduplication
  -> PostgreSQL
  -> Records UI / CSV / XLSX / DRF API
```

## Scraping layers

- `validators/`: HTTP/HTTPS and DNS/IP safety checks, including redirects
- `fetchers/`: ordinary HTTP fetching
- `strategies/`: BeautifulSoup, Playwright and Selenium fetch/render implementations
- `extractors/`: generic metadata and structured entity extraction
- `pagination/`: bounded same-domain next-page discovery
- `pipeline/`: strategy selection and orchestration
- `exceptions/`: user-safe scraping errors

The browser is not launched for a normal static page when the automatic strategy can extract useful content with HTTP.

## Persistence

`ScrapeJob` stores URL, strategy, limits, custom selectors and scheduling configuration.

`JobRun` stores execution state, timestamps, duration, records found/created, strategy used and errors.

`ScrapedRecord` stores common normalized fields plus JSON fields for website-specific metadata and structured data. `(job, content_hash)` is unique to prevent uncontrolled duplicates.

## Scheduling

`django-celery-beat` stores an `IntervalSchedule` and `PeriodicTask` per scheduled job. Atlas supports hourly, daily and weekly intervals. The actual scraping work is always executed by Celery, not by the Django request thread.

## Security

Every user URL is validated before fetching. Hostnames are resolved and private, loopback, link-local, multicast, reserved, unspecified, localhost and known metadata/internal hostnames are rejected. Redirect destinations are independently validated. Object-level ownership filters scope every UI and API query to the authenticated user.
