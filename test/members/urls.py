from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("customfunctions/", views.customfunctions, name="customfunctions"),
    path("customfunctions/addition/", views.addition, name="addition"),
    path("customfunctions/subtraction/", views.subtraction, name="subtraction"),
    path(
        "customfunctions/multiplication/", views.multiplication, name="multiplication"
    ),
    path("login_form/", views.login_form, name="login_form"),
    path("logoutsite/", views.logoutsite, name="logoutsite"),
    path("customfunctions/time_function/", views.time_function, name="time_function"),
    path("celery-progress/", include("celery_progress.urls")),
    path("output-site/", views.output_site, name="output_site"),
    path(
        "output-site/task-details/<str:uuid>", views.task_details, name="task_details"
    ),
    path("alarms_uni/", views.alarms_uni, name="alarms_uni"),
    path(
        "download/<str:user_id>/<str:output_xlsx>/<str:og_output_xlsx>",
        views.download,
        name="download",
    ),
]
