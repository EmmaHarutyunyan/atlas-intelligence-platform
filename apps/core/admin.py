from django.contrib import admin

from .models import JobRun, ScrapeJob, ScrapedRecord


@admin.register(ScrapeJob)
class ScrapeJobAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "strategy", "status", "schedule_enabled", "records_count", "last_run", "created_at")
    list_filter = ("status", "strategy", "schedule_enabled", "schedule_frequency")
    search_fields = ("name", "url", "user__username")
    readonly_fields = ("run_count", "records_count", "last_run", "created_at", "updated_at")


@admin.register(ScrapedRecord)
class ScrapedRecordAdmin(admin.ModelAdmin):
    list_display = ("title", "record_type", "job", "confidence", "created_at")
    list_filter = ("record_type", "confidence", "created_at")
    search_fields = ("title", "url", "description", "content")
    readonly_fields = ("content_hash", "created_at", "updated_at")


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    list_display = ("job", "status", "records_found", "records_created", "strategy_used", "started_at", "duration_seconds")
    list_filter = ("status", "strategy_used", "started_at")
    search_fields = ("job__name", "error_message")
    readonly_fields = ("started_at", "finished_at", "duration_seconds")
