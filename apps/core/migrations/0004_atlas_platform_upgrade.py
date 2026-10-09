from django.db import migrations, models
from django.core.validators import MaxValueValidator, MinValueValidator


class Migration(migrations.Migration):
    dependencies = [("core", "0003_remove_scrapedrecord_availability_and_more")]

    operations = [
        migrations.AddField(model_name="scrapejob", name="schedule_frequency", field=models.CharField(choices=[("hourly", "Hourly"), ("daily", "Daily"), ("weekly", "Weekly")], default="daily", max_length=20)),
        migrations.AddField(model_name="scrapejob", name="custom_fields", field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name="scrapejob", name="max_pages", field=models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(20)])),
        migrations.AddField(model_name="scrapejob", name="max_records", field=models.PositiveIntegerField(default=200, validators=[MinValueValidator(1), MaxValueValidator(5000)])),
        migrations.AddField(model_name="scrapejob", name="request_timeout", field=models.PositiveIntegerField(default=20, validators=[MinValueValidator(5), MaxValueValidator(120)])),
        migrations.AddField(model_name="scrapejob", name="request_delay", field=models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])),
        migrations.AlterField(model_name="scrapejob", name="strategy", field=models.CharField(choices=[("automatic", "Automatic"), ("beautifulsoup", "BeautifulSoup"), ("playwright", "Playwright"), ("selenium", "Selenium")], default="automatic", max_length=30)),
        migrations.AddIndex(model_name="scrapejob", index=models.Index(fields=["user", "status"], name="core_scrapej_user_id_7f0b34_idx")),
        migrations.AddIndex(model_name="scrapejob", index=models.Index(fields=["user", "created_at"], name="core_scrapej_user_id_9d6a4b_idx")),
        migrations.AddField(model_name="scrapedrecord", name="source_url", field=models.URLField(blank=True)),
        migrations.AddField(model_name="scrapedrecord", name="record_type", field=models.CharField(db_index=True, default="page", max_length=50)),
        migrations.AddField(model_name="scrapedrecord", name="description", field=models.TextField(blank=True)),
        migrations.AddField(model_name="scrapedrecord", name="image_url", field=models.URLField(blank=True)),
        migrations.AddField(model_name="scrapedrecord", name="confidence", field=models.CharField(default="Low", max_length=20)),
        migrations.AddField(model_name="scrapedrecord", name="metadata", field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name="scrapedrecord", name="structured_data", field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name="scrapedrecord", name="updated_at", field=models.DateTimeField(auto_now=True)),
        migrations.AddIndex(model_name="scrapedrecord", index=models.Index(fields=["job", "created_at"], name="core_scrapej_job_id_9d7d4f_idx")),
        migrations.AddIndex(model_name="scrapedrecord", index=models.Index(fields=["record_type", "created_at"], name="core_scraped_record_6d1f4a_idx")),
        migrations.AddField(model_name="jobrun", name="duration_seconds", field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name="jobrun", name="strategy_used", field=models.CharField(blank=True, max_length=30)),
        migrations.AddIndex(model_name="jobrun", index=models.Index(fields=["job", "started_at"], name="core_jobrun_job_id_4ef7f5_idx")),
    ]
