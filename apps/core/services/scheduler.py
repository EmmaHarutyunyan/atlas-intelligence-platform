import json

from django_celery_beat.models import IntervalSchedule, PeriodicTask


def sync_job_schedule(job):
    task_name = f"atlas-job-{job.pk}"
    if not job.schedule_enabled:
        PeriodicTask.objects.filter(name=task_name).delete()
        return

    every, period = {"hourly": (1, IntervalSchedule.HOURS), "daily": (1, IntervalSchedule.DAYS), "weekly": (7, IntervalSchedule.DAYS)}[job.schedule_frequency]
    schedule, _ = IntervalSchedule.objects.get_or_create(every=every, period=period)
    task, _ = PeriodicTask.objects.get_or_create(name=task_name, defaults={"task": "apps.core.tasks.run_scheduled_job"})
    task.task = "apps.core.tasks.run_scheduled_job"
    task.interval = schedule
    task.args = json.dumps([job.pk])
    task.enabled = True
    task.save()
