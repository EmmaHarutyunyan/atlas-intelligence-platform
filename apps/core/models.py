from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ScrapeJob(models.Model):
    STRATEGY_CHOICES = [
        ("automatic", "Automatic"),
        ("beautifulsoup", "BeautifulSoup"),
        ("playwright", "Playwright"),
        ("selenium", "Selenium"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"), ("running", "Running"), ("completed", "Completed"),
        ("failed", "Failed"), ("cancelled", "Cancelled"),
    ]
    SCHEDULE_CHOICES = [("hourly", "Hourly"), ("daily", "Daily"), ("weekly", "Weekly")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scrape_jobs")
    name = models.CharField(max_length=150)
    url = models.URLField()
    strategy = models.CharField(max_length=30, choices=STRATEGY_CHOICES, default="automatic")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    schedule_enabled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, default="daily")
    custom_fields = models.JSONField(default=dict, blank=True)
    max_pages = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(20)])
    max_records = models.PositiveIntegerField(default=200, validators=[MinValueValidator(1), MaxValueValidator(5000)])
    request_timeout = models.PositiveIntegerField(default=20, validators=[MinValueValidator(5), MaxValueValidator(120)])
    request_delay = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    run_count = models.PositiveIntegerField(default=0)
    records_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["user", "status"]), models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return self.name


class ScrapedRecord(models.Model):
    job = models.ForeignKey(ScrapeJob, on_delete=models.CASCADE, related_name="records")
    source_url = models.URLField(blank=True)
    record_type = models.CharField(max_length=50, default="page", db_index=True)
    title = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    confidence = models.CharField(max_length=20, default="Low")
    metadata = models.JSONField(default=dict, blank=True)
    structured_data = models.JSONField(default=list, blank=True)
    data = models.JSONField(default=dict, blank=True)
    content_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["job", "content_hash"], name="unique_record_per_job")]
        indexes = [models.Index(fields=["job", "created_at"]), models.Index(fields=["record_type", "created_at"])]

    def __str__(self):
        return self.title or self.url or f"Record {self.id}"


class JobRun(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"), ("running", "Running"), ("completed", "Completed"),
        ("failed", "Failed"), ("cancelled", "Cancelled"),
    ]
    job = models.ForeignKey(ScrapeJob, on_delete=models.CASCADE, related_name="runs")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    records_found = models.PositiveIntegerField(default=0)
    records_created = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    strategy_used = models.CharField(max_length=30, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=["job", "started_at"])]

    def __str__(self):
        return f"{self.job.name} - {self.started_at}"
