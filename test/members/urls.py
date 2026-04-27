from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login_form/", views.login_form, name="login_form"),
    path("logoutsite/", views.logoutsite, name="logoutsite"),
    path("time_function/", views.time_function, name="time_function"),
    path("celery-progress/", include("celery_progress.urls")),
    path("output-site/", views.output_site, name="output_site"),
    path(
        "output-site/task-details/<str:uuid>/", views.task_details, name="task_details"
    ),
    path("alarms_uni/", views.alarms_uni, name="alarms_uni"),
    path(
        "download/<str:user_id>/<str:output_xlsx>/<str:og_output_xlsx>/<str:folder_name>/",
        views.download,
        name="download",
    ),
    path("pf_ad_trans/", views.pf_ad_trans, name="pf_ad_trans"),
    path("xlsx_merge/", views.xlsx_merge, name="xlsx_merge"),
    path("check_status/<str:task_id>/", views.check_status, name="check_status"),
    path("output-site/logs/<str:task_id>/", views.task_logs, name="task_logs"),
]
