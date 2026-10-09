from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import JobRun, ScrapeJob, ScrapedRecord
from ..tasks import run_scrape_job
from .serializers import JobRunSerializer, ScrapeJobSerializer, ScrapedRecordSerializer


class JobViewSet(viewsets.ModelViewSet):
    serializer_class = ScrapeJobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ScrapeJob.objects.filter(user=self.request.user).annotate(records_count=Count("records")).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        job = self.get_object()
        if job.status == "running":
            return Response({"detail": "This job is already running."}, status=status.HTTP_409_CONFLICT)
        job_run = JobRun.objects.create(job=job, status="pending")
        task = run_scrape_job.delay(job.pk, job_run.pk)
        return Response({"run_id": job_run.pk, "task_id": task.id, "status": "pending"}, status=status.HTTP_202_ACCEPTED)


class RecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ScrapedRecordSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["title", "description", "content", "url", "record_type"]
    ordering_fields = ["created_at", "updated_at", "title", "record_type"]

    def get_queryset(self):
        return ScrapedRecord.objects.filter(job__user=self.request.user).select_related("job").order_by("-created_at")


class RunViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JobRunSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return JobRun.objects.filter(job__user=self.request.user).select_related("job").order_by("-started_at")
