import ast
import os
import time

import requests
from celery import current_app
from celery.result import AsyncResult
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect, render
from django.template import loader

from .tasks import add, alarms_tp_uni, mult, sub, timer
from .utility import send_data


def index(request):
    send_data(request)
    return HttpResponse(loader.get_template("index.html").render())


def customfunctions(request):
    send_data(request)
    return HttpResponse(loader.get_template("customfunctions.html").render())


def addition(request):
    send_data(request)
    if request.user.is_authenticated:
        if request.method == "POST":
            num1 = int(request.POST.get("num1", 0))
            num2 = int(request.POST.get("num2", 0))
            if isinstance(num1, int) and isinstance(num2, int):
                return HttpResponse(
                    loader.get_template("addition.html").render(
                        {"x": add.delay(num1, num2, user_id=request.user.id).get},
                        request,
                    )
                )
        else:
            return render(request, "addition.html")
    else:
        return HttpResponse(loader.get_template("access_denied.html").render())


def subtraction(request):
    send_data(request)
    if request.user.is_authenticated:
        if request.method == "POST":
            num1 = int(request.POST.get("num1", 0))
            num2 = int(request.POST.get("num2", 0))
            if isinstance(num1, int) and isinstance(num2, int):
                return HttpResponse(
                    loader.get_template("subtraction.html").render(
                        {"x": sub.delay(num1, num2, user_id=request.user.id).get},
                        request,
                    )
                )
        else:
            return render(request, "subtraction.html")
    else:
        return HttpResponse(loader.get_template("access_denied.html").render())


def multiplication(request):
    send_data(request)
    if request.user.is_authenticated and request.user.has_perm(
        "members.multiplication_access"
    ):
        if request.method == "POST":
            num1 = int(request.POST.get("num1", 0))
            num2 = int(request.POST.get("num2", 0))
            if isinstance(num1, int) and isinstance(num2, int):
                return HttpResponse(
                    loader.get_template("multiplication.html").render(
                        {"x": mult.delay(num1, num2, user_id=request.user.id).get},
                        request,
                    )
                )
        return render(request, "multiplication.html")
    else:
        return HttpResponse(loader.get_template("access_denied.html").render())


def time_function(request):
    send_data(request)
    if request.user.is_authenticated:
        task_id = cache.get(f"user_task_timer_{request.user.id}")
        if request.method == "POST":
            action = request.POST.get("action")
            if action == "delete" and task_id:
                current_app.control.revoke(task_id, terminate=True, signal="KILL")
                cache.delete(f"user_task_timer_{request.user.id}")
                task_id = None
                return redirect("time_function")
            elif action != "delete" and not task_id:
                task = timer.delay(
                    int(request.POST.get("time_left", 1)), user_id=request.user.id
                )
                task_id = task.id
                cache.set(f"user_task_timer_{request.user.id}", task_id, timeout=21600)
                return redirect("time_function")
        if task_id:
            if AsyncResult(task_id).ready():
                cache.delete(f"user_task_timer_{request.user.id}")
                task_id = None
        return render(request, "timer.html", {"task_id": task_id})
    else:
        return render(request, "access_denied.html")


def login_form(request):
    if request.user.is_authenticated:
        return redirect("index")
    else:
        context = {}
        if request.method == "POST":
            form = AuthenticationForm(data=request.POST)
            if form.is_valid():
                login(request, form.get_user())
                return redirect("index")
            else:
                context = {
                    "statusCode": "Invalid login",
                }
        else:
            form = AuthenticationForm()
        template = loader.get_template("login_form.html")
        return HttpResponse(template.render(context, request))


def logoutsite(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect("login_form")
    else:
        return redirect("index")


def output_site(request):
    send_data(request)
    if request.user.is_authenticated:
        user_tasks = []
        for task_id, task_data in (
            requests.get("http://flower:5555/api/tasks", timeout=2).json().items()
        ):
            raw_kwargs = task_data["kwargs"].replace("\n", "").replace("\r", "")
            if ast.literal_eval(raw_kwargs)["user_id"] == request.user.id:
                task_data["uuid"] = task_id
                task_data["started"] = time.ctime(task_data["started"])
                user_tasks.append(task_data)
        return render(request, "output_site.html", {"tasks": user_tasks})
    else:
        return render(request, "access_denied.html")


def task_details(request, uuid):
    send_data(request)
    if request.user.is_authenticated:
        item = requests.get(
            f"http://flower:5555/api/task/info/{uuid}", timeout=2
        ).json()
        raw_kwargs = item["kwargs"].replace("\n", "").replace("\r", "")
        if ast.literal_eval(raw_kwargs)["user_id"] == request.user.id:
            return render(
                request,
                "task_details.html",
                {"task": item},
            )
        else:
            return render(request, "access_denied.html")
    else:
        return render(request, "access_denied.html")


def alarms_uni(request):
    send_data(request)
    if request.user.is_authenticated:
        task_id = cache.get(f"user_task_alarms_{request.user.id}")
        if request.method == "POST":
            input_xlsx = request.FILES.get("input_xlsx")
            output_xlsx = request.POST.get("output_xlsx")
            if not output_xlsx.lower().endswith(".xlsx"):
                output_xlsx += ".xlsx"
            input_txt = request.FILES.get("input_txt")
            if input_xlsx and output_xlsx and input_txt:
                task = alarms_tp_uni.delay(
                    input_xlsx=default_storage.path(
                        default_storage.save(f"{input_xlsx.name}", input_xlsx)
                    ),
                    output_xlsx=output_xlsx,
                    input_txt=",\n".join(
                        f'"{txt}"'
                        for txt in input_txt.read().decode("utf-8").splitlines()
                    ),
                    user_id=request.user.id,
                )
                task_id = task.id
                cache.set(f"user_task_alarms_{request.user.id}", task_id, timeout=1800)
                return redirect("alarms_uni")
            else:
                return redirect("alarms_uni")
        if task_id:
            if AsyncResult(task_id).ready():
                cache.delete(f"user_task_alarms_{request.user.id}")
                task_id = None
                return redirect("output_site")
        return render(request, "alarms_uni.html", {"task_id": task_id})
    else:
        return render(request, "access_denied.html")


def download(request, user_id, output_xlsx, og_output_xlsx):
    if request.user.is_authenticated and str(request.user.id) == user_id:
        return FileResponse(
            open(
                os.path.join(f"UserFiles/{user_id}", output_xlsx),
                "rb",
            ),
            as_attachment=True,
            filename=og_output_xlsx,
        )
    else:
        return render(request, "access_denied.html")
