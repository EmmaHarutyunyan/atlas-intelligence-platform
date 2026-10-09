from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import JobViewSet, RecordViewSet, RunViewSet

router = DefaultRouter()
router.register("jobs", JobViewSet, basename="api-job")
router.register("records", RecordViewSet, basename="api-record")
router.register("runs", RunViewSet, basename="api-run")

urlpatterns = [
    path("", include(router.urls)),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
