import ast
import glob
import json
import os
import time

import requests
from celery import current_app
from celery.result import AsyncResult
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template import loader

from .models import Tools
from .tasks import (
    alarms_tp_uni,
    merge_xlsx,
    proface_adress_translate,
    timer,
)
from .utility import send_data


def index(request):
    send_data(request)
    return HttpResponse(loader.get_template("index.html").render())


def time_function(request):
    send_data(request)
    if not request.user.is_authenticated:
        return render(request, "access_denied.html")
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
    if not request.user.is_authenticated:
        return render(request, "access_denied.html")
    user_tasks = []
    for task_id, task_data in (
        requests.get("http://flower:5555/api/tasks", timeout=2).json().items()
    ):
        if (
            ast.literal_eval(
                task_data["kwargs"].replace("\n", "").replace("\r", "")
            ).get("user_id")
            == request.user.id
        ):
            task_data["uuid"] = task_id
            task_data["started"] = time.ctime(task_data["started"])
            user_tasks.append(task_data)
    return render(
        request,
        "output_site.html",
        {
            "tasks": user_tasks,
            "task_list": [task["uuid"] for task in user_tasks],
        },
    )


def task_details(request, uuid):
    send_data(request)
    if not request.user.is_authenticated:
        return render(request, "access_denied.html")
    item = requests.get(f"http://flower:5555/api/task/info/{uuid}", timeout=2)
    if item:
        item = item.json()
    elif not item or "kwargs" not in item:
        return render(request, "access_denied.html")
    if (
        ast.literal_eval(item["kwargs"].replace("\n", "").replace("\r", ""))["user_id"]
        == request.user.id
    ):
        return render(
            request,
            "task_details.html",
            {"task": item},
        )
    else:
        return render(request, "access_denied.html")


def alarms_uni(request):
    send_data(request)
    if not request.user.is_authenticated:
        return render(request, "access_denied.html")
    task_id = cache.get(f"user_task_alarms_{request.user.id}")
    context = {"tool": Tools.objects.filter(tool_id=1).first()}
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
                    f'"{txt}"' for txt in input_txt.read().decode("utf-8").splitlines()
                ),
                user_id=request.user.id,
            )
            task_id = task.id
            cache.set(f"user_task_alarms_{request.user.id}", task_id, timeout=1800)
            return redirect("alarms_uni")
    else:
        if task_id:
            if AsyncResult(task_id).ready():
                cache.delete(f"user_task_alarms_{request.user.id}")
                context["button"] = AsyncResult(task_id).get()
                return render(request, "alarms_uni.html", context)
        context["task_id"] = task_id
        return render(request, "alarms_uni.html", context)
    return render(request, "alarms_uni.html", context)


def download(request, user_id, output_xlsx, og_output_xlsx, folder_name):
    send_data(request)
    if not request.user.is_authenticated or not str(request.user.id) == user_id:
        return render(request, "access_denied.html")
    return FileResponse(
        open(
            os.path.join(f"UserFiles/{user_id}/{folder_name}", output_xlsx),
            "rb",
        ),
        as_attachment=True,
        filename=og_output_xlsx,
    )


def pf_ad_trans(request):
    send_data(request)
    if not request.user.is_authenticated:
        return render(request, "access_denied.html")
    context = {"tool": Tools.objects.filter(tool_id=1).first()}
    if request.method == "POST":
        try:
            return JsonResponse(
                {
                    "status": "success",
                    "values": proface_adress_translate.delay(
                        json.loads(request.body), user_id=request.user.id
                    ).get(),
                }
            )
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "values": "Invalid JSON"}, status=400
            )
    return render(request, "pf_ad_trans.html", context)


def xlsx_merge(request):
    send_data(request)
    if not request.user.is_authenticated:
        return render(request, "access_denied.html")
    context = {"tool": Tools.objects.filter(tool_id=1).first()}
    task_id = cache.get(f"user_task_merge_{request.user.id}")
    if request.method == "POST":
        og_xlsx = request.FILES.get("og_xlsx")
        og_names = request.POST.get("og_names")
        og_values = request.POST.get("og_values")
        fix_xlsx = request.FILES.get("fix_xlsx")
        fix_names = request.POST.get("fix_names")
        fix_values = request.POST.get("fix_values")
        output_xlsx = request.POST.get("output_xlsx")
        if (
            og_xlsx is not None
            and og_names != ""
            and og_values != ""
            and fix_xlsx is not None
            and fix_names != ""
            and fix_values != ""
            and output_xlsx != ""
        ):
            if not output_xlsx.lower().endswith(".xlsx"):
                output_xlsx += ".xlsx"
                task = merge_xlsx.delay(
                    default_storage.path(
                        default_storage.save(f"{og_xlsx.name}", og_xlsx)
                    ),
                    og_names,
                    og_values,
                    default_storage.path(
                        default_storage.save(f"{fix_xlsx.name}", fix_xlsx)
                    ),
                    fix_names,
                    fix_values,
                    output_xlsx,
                    user_id=request.user.id,
                )
            task_id = task.id
            cache.set(f"user_task_merge_{request.user.id}", task_id, timeout=3600)
            return redirect("xlsx_merge")
    else:
        if task_id:
            if AsyncResult(task_id).ready():
                cache.delete(f"user_task_merge_{request.user.id}")
                context["button"] = AsyncResult(task_id).get()
                return render(request, "xlsx_merge.html", context)
        context["task_id"] = task_id
        return render(request, "xlsx_merge.html", context)
    return render(request, "xlsx_merge.html", context)


def check_status(request, task_id):
    send_data(request)
    return JsonResponse({"status": AsyncResult(task_id).status})


def task_logs(request, task_id):
    send_data(request)
    if not request.user.is_authenticated:
        return render(request, "access_denied.html")
    item = requests.get(f"http://flower:5555/api/task/info/{task_id}", timeout=2)
    if item:
        item = item.json()
    elif not item or "kwargs" not in item:
        return render(request, "access_denied.html")
    if (
        ast.literal_eval(item["kwargs"].replace("\n", "").replace("\r", ""))["user_id"]
        != request.user.id
    ):
        return render(request, "access_denied.html")
    found_files = []
    found_files = glob.glob(os.path.join("/app/test/logs/", "debug_*.log"))
    found_files.sort(key=os.path.getmtime, reverse=True)
    logs = []
    for file_path in found_files[:3]:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if task_id in line and "WSGIRequest" not in line:
                    logs.append(line)
    return render(
        request,
        "task_logs.html",
        {"logs": logs, "task_id": task_id},
    )
