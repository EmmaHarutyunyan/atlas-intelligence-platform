import csv
import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from openpyxl import Workbook

from .forms import ScrapeJobForm
from .models import JobRun, ScrapeJob, ScrapedRecord
from .services.scheduler import sync_job_schedule
from .tasks import run_scrape_job


def home(request):
    return render(request, "home.html")


@login_required
def dashboard(request):
    jobs = ScrapeJob.objects.filter(user=request.user).order_by("-created_at")
    total_records = ScrapedRecord.objects.filter(job__user=request.user).count()
    recent_runs = JobRun.objects.filter(job__user=request.user).select_related("job").order_by("-started_at")[:10]
    context = {
        "jobs": jobs,
        "total_jobs": jobs.count(),
        "total_records": total_records,
        "completed_jobs": jobs.filter(status="completed").count(),
        "failed_jobs": jobs.filter(status="failed").count(),
        "running_jobs": jobs.filter(status="running").count(),
        "recent_runs": recent_runs,
        "records_by_job": list(ScrapedRecord.objects.filter(job__user=request.user).values("job__name").annotate(count=Count("id")).order_by("-count")[:10]),
    }
    return render(request, "dashboard.html", context)


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        return redirect("dashboard")
    return render(request, "register.html", {"form": form})


@login_required
def create_job(request):
    form = ScrapeJobForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.user = request.user
        job.save()
        sync_job_schedule(job)
        messages.success(request, "Scraping job created successfully.")
        return redirect("job_detail", job_id=job.id)
    return render(request, "jobs/create.html", {"form": form})


@login_required
def edit_job(request, job_id):
    job = get_object_or_404(ScrapeJob, id=job_id, user=request.user)
    form = ScrapeJobForm(request.POST or None, instance=job)
    if request.method == "POST" and form.is_valid():
        job = form.save()
        sync_job_schedule(job)
        messages.success(request, "Scraping job updated.")
        return redirect("job_detail", job_id=job.id)
    return render(request, "jobs/create.html", {"form": form, "editing": True, "job": job})


@login_required
def job_detail(request, job_id):
    job = get_object_or_404(ScrapeJob, id=job_id, user=request.user)
    records = job.records.order_by("-created_at")[:20]
    runs = job.runs.order_by("-started_at")[:10]
    return render(request, "jobs/detail.html", {"job": job, "records": records, "runs": runs})


@login_required
def run_job(request, job_id):
    job = get_object_or_404(ScrapeJob, id=job_id, user=request.user)
    if request.method != "POST":
        return redirect("job_detail", job_id=job.id)
    if job.status == "running":
        messages.warning(request, "This job is already running.")
        return redirect("job_detail", job_id=job.id)
    run = JobRun.objects.create(job=job, status="pending")
    task = run_scrape_job.delay(job.pk, run.pk)
    messages.success(request, f"Run queued successfully. Task: {task.id[:12]}…")
    return redirect("job_detail", job_id=job.id)


@login_required
def delete_job(request, job_id):
    job = get_object_or_404(ScrapeJob, id=job_id, user=request.user)
    if request.method == "POST":
        from django_celery_beat.models import PeriodicTask
        PeriodicTask.objects.filter(name=f"atlas-job-{job.pk}").delete()
        job.delete()
        messages.success(request, "Job deleted.")
        return redirect("dashboard")
    return render(request, "jobs/delete.html", {"job": job})


@login_required
def records(request):
    queryset = ScrapedRecord.objects.filter(job__user=request.user).select_related("job")
    search = request.GET.get("search", "").strip()
    record_type = request.GET.get("type", "").strip()
    job_id = request.GET.get("job", "").strip()
    ordering = request.GET.get("ordering", "-created_at")
    allowed_ordering = {"created_at", "-created_at", "title", "-title", "record_type", "-record_type"}
    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search) | Q(content__icontains=search))
    if record_type:
        queryset = queryset.filter(record_type=record_type)
    if job_id.isdigit():
        queryset = queryset.filter(job_id=int(job_id))
    queryset = queryset.order_by(ordering if ordering in allowed_ordering else "-created_at")
    paginator = Paginator(queryset, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {"records": page_obj, "page_obj": page_obj, "search": search, "record_type": record_type, "job_id": job_id, "jobs": ScrapeJob.objects.filter(user=request.user), "record_types": ScrapedRecord.objects.filter(job__user=request.user).values_list("record_type", flat=True).distinct().order_by("record_type")}
    return render(request, "records/list.html", context)


@login_required
def delete_record(request, record_id):
    record = get_object_or_404(ScrapedRecord, id=record_id, job__user=request.user)
    if request.method == "POST":
        record.delete()
        messages.success(request, "Record deleted.")
    return redirect("records")


@login_required
def analytics(request):
    runs = JobRun.objects.filter(job__user=request.user)
    total_records = ScrapedRecord.objects.filter(job__user=request.user).count()
    successful = runs.filter(status="completed").count()
    failed = runs.filter(status="failed").count()
    context = {"jobs": ScrapeJob.objects.filter(user=request.user), "total_records": total_records, "total_runs": runs.count(), "successful_runs": successful, "failed_runs": failed, "category_data": list(ScrapedRecord.objects.filter(job__user=request.user).values("record_type").annotate(count=Count("id")).order_by("-count"))}
    return render(request, "analytics.html", context)


def _filtered_records(request):
    queryset = ScrapedRecord.objects.filter(job__user=request.user).select_related("job")
    search = request.GET.get("search", "").strip()
    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search) | Q(content__icontains=search))
    if request.GET.get("type"):
        queryset = queryset.filter(record_type=request.GET["type"])
    if request.GET.get("job", "").isdigit():
        queryset = queryset.filter(job_id=int(request.GET["job"]))
    return queryset.order_by("-created_at")


@login_required
def export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="atlas_records.csv"'
    writer = csv.writer(response)
    writer.writerow(["Title", "Type", "Price", "Rating", "Availability", "URL", "Image", "Confidence", "Job", "Created"])
    for record in _filtered_records(request):
        attrs = record.data.get("attributes", {})
        writer.writerow([record.title, record.record_type, attrs.get("price", ""), attrs.get("rating", ""), attrs.get("availability", ""), record.url, record.image_url, record.confidence, record.job.name, record.created_at])
    return response


@login_required
def export_xlsx(request):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Atlas Records"
    sheet.append(["Title", "Type", "Price", "Rating", "Availability", "URL", "Image", "Confidence", "Job", "Created"])
    for record in _filtered_records(request):
        attrs = record.data.get("attributes", {})
        sheet.append([record.title, record.record_type, attrs.get("price", ""), attrs.get("rating", ""), attrs.get("availability", ""), record.url, record.image_url, record.confidence, record.job.name, record.created_at])
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="atlas_records.xlsx"'
    workbook.save(response)
    return response


@login_required
def record_detail(request, record_id):
    record = get_object_or_404(ScrapedRecord, id=record_id, job__user=request.user)
    return render(request, "records/detail.html", {"record": record})
