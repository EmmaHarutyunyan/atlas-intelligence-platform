
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("register/", views.register, name="register"),

    path("jobs/create/", views.create_job, name="create_job"),
    path("jobs/<int:job_id>/", views.job_detail, name="job_detail"),
    path("jobs/<int:job_id>/edit/", views.edit_job, name="edit_job"),
    path("jobs/<int:job_id>/run/", views.run_job, name="run_job"),
    path("jobs/<int:job_id>/delete/", views.delete_job, name="delete_job"),

    path("records/", views.records, name="records"),
    path("records/<int:record_id>/", views.record_detail, name="record_detail"),
    path("records/<int:record_id>/delete/", views.delete_record, name="delete_record"),

    path("analytics/", views.analytics, name="analytics"),
    path("export/csv/", views.export_csv, name="export_csv"),
    path("export/xlsx/", views.export_xlsx, name="export_xlsx"),

    path(
        "login/",
        auth_views.LoginView.as_view(template_name="login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="password_reset/form.html"
        ),
        name="password_reset_form",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset/done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset/confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset/complete.html"
        ),
        name="password_reset_complete",
    ),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]