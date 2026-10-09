from rest_framework import serializers

from ..models import JobRun, ScrapeJob, ScrapedRecord


class ScrapedRecordSerializer(serializers.ModelSerializer):
    job_name = serializers.CharField(source="job.name", read_only=True)

    class Meta:
        model = ScrapedRecord
        fields = ["id", "job", "job_name", "source_url", "record_type", "title", "description", "content", "url", "image_url", "confidence", "metadata", "structured_data", "data", "content_hash", "created_at", "updated_at"]
        read_only_fields = ["content_hash", "created_at", "updated_at", "job_name"]


class JobRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRun
        fields = ["id", "job", "status", "records_found", "records_created", "started_at", "finished_at", "duration_seconds", "strategy_used", "error_message"]
        read_only_fields = fields


class ScrapeJobSerializer(serializers.ModelSerializer):
    records_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ScrapeJob
        fields = ["id", "name", "url", "strategy", "status", "schedule_enabled", "schedule_frequency", "custom_fields", "max_pages", "max_records", "request_timeout", "request_delay", "run_count", "records_count", "error_message", "last_run", "created_at", "updated_at"]
        read_only_fields = ["status", "run_count", "records_count", "error_message", "last_run", "created_at", "updated_at"]
