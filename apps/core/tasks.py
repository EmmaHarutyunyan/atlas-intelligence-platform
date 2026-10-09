import logging
import time

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import JobRun, ScrapeJob, ScrapedRecord
from .services.scraping import scrape

logger = logging.getLogger(__name__)


def _run_job(job_id: int, run_id: int | None = None):
    job = ScrapeJob.objects.get(pk=job_id)
    run = JobRun.objects.get(pk=run_id) if run_id else JobRun.objects.create(job=job, status="pending")
    started = time.monotonic()
    run.status = "running"
    run.save(update_fields=["status"])
    job.status = "running"
    job.error_message = ""
    job.save(update_fields=["status", "error_message", "updated_at"])
    logger.info("Atlas job started: job=%s run=%s", job.pk, run.pk)

    try:
        result = scrape(job.url, job.strategy, job.custom_fields, job.max_pages, job.max_records, job.request_timeout, job.request_delay)
        records = result.get("records", [])[: job.max_records]
        created_count = 0
        with transaction.atomic():
            for item in records:
                defaults = {
                    "source_url": result["url"], "record_type": item.get("record_type", result.get("record_type", "page")),
                    "title": item.get("title", "")[:500], "description": item.get("description", ""),
                    "content": item.get("content", result.get("content", "")), "url": item.get("url", result["url"]),
                    "image_url": item.get("image_url", ""), "confidence": result.get("confidence", "Low"),
                    "metadata": result["data"].get("metadata", {}), "structured_data": item.get("structured_data", result.get("structured_data", [])),
                    "data": {**result["data"], "attributes": item.get("attributes", {})},
                }
                _, created = ScrapedRecord.objects.update_or_create(job=job, content_hash=item["content_hash"], defaults=defaults)
                created_count += int(created)
        job.run_count += 1
        job.records_count = job.records.count()
        job.status = "completed"
        job.last_run = timezone.now()
        job.save(update_fields=["run_count", "records_count", "status", "last_run", "updated_at"])
        run.status = "completed"
        run.records_found = len(records)
        run.records_created = created_count
        run.strategy_used = result.get("strategy_used", "")
        run.finished_at = timezone.now()
        run.duration_seconds = round(time.monotonic() - started, 3)
        run.save()
        logger.info("Atlas job completed: job=%s run=%s records=%s", job.pk, run.pk, len(records))
        return {"run_id": run.pk, "records_found": len(records), "records_created": created_count}
    except Exception as exc:
        message = str(exc)
        job.status = "failed"
        job.error_message = message[:2000]
        job.save(update_fields=["status", "error_message", "updated_at"])
        run.status = "failed"
        run.error_message = message[:2000]
        run.finished_at = timezone.now()
        run.duration_seconds = round(time.monotonic() - started, 3)
        run.save()
        logger.exception("Atlas job failed: job=%s run=%s", job.pk, run.pk)
        raise


@shared_task(bind=True, autoretry_for=(), name="apps.core.tasks.run_scrape_job")
def run_scrape_job(self, job_id: int, run_id: int):
    return _run_job(job_id, run_id)


@shared_task(name="apps.core.tasks.run_scheduled_job")
def run_scheduled_job(job_id: int):
    job = ScrapeJob.objects.get(pk=job_id)
    if not job.schedule_enabled or job.status == "running":
        return {"skipped": True}
    run = JobRun.objects.create(job=job, status="pending")
    return _run_job(job.pk, run.pk)
