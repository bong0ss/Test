import ast
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
    add,
    alarms_tp_uni,
    merge_xlsx,
    mult,
    proface_adress_translate,
    sub,
    timer,
)
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
            if ast.literal_eval(raw_kwargs).get("user_id") == request.user.id:
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
        if not item:
            return render(request, "access_denied.html")
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
                        f'"{txt}"'
                        for txt in input_txt.read().decode("utf-8").splitlines()
                    ),
                    user_id=request.user.id,
                )
                task_id = task.id
                cache.set(f"user_task_alarms_{request.user.id}", task_id, timeout=1800)
                return redirect("alarms_uni")
            else:
                return render(request, "alarms_uni.html", context)
        if task_id:
            if AsyncResult(task_id).ready():
                cache.delete(f"user_task_alarms_{request.user.id}")
                context["button"] = AsyncResult(task_id).get()
                return render(request, "alarms_uni.html", context)
        return render(request, "alarms_uni.html", context)
    else:
        return render(request, "access_denied.html")


def download(request, user_id, output_xlsx, og_output_xlsx, folder_name):
    send_data(request)
    if request.user.is_authenticated and str(request.user.id) == user_id:
        return FileResponse(
            open(
                os.path.join(f"UserFiles/{user_id}/{folder_name}", output_xlsx),
                "rb",
            ),
            as_attachment=True,
            filename=og_output_xlsx,
        )
    else:
        return render(request, "access_denied.html")


def pf_ad_trans(request):
    send_data(request)
    if request.user.is_authenticated:
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
    else:
        return render(request, "access_denied.html")


def xlsx_merge(request):
    send_data(request)
    if request.user.is_authenticated:
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
                return render(request, "xlsx_merge.html", context)
        if task_id:
            if AsyncResult(task_id).ready():
                cache.delete(f"user_task_merge_{request.user.id}")
                context["button"] = AsyncResult(task_id).get()
                return render(request, "xlsx_merge.html", context)
        return render(request, "xlsx_merge.html", context)
    else:
        return render(request, "access_denied.html")
