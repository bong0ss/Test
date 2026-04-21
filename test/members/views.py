import ast
import time

import requests
from celery import current_app
from celery.result import AsyncResult
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template import loader

from .models import Member, PcComp
from .tasks import add, mult, sub, timer
from .utility import send_data


def members(request):
    send_data(request)
    return HttpResponse(
        loader.get_template("members.html").render(
            {
                "mymembers": Member.objects.all().values(),
            },
            request,
        )
    )


def details(request, id):
    send_data(request)
    return HttpResponse(
        loader.get_template("details.html").render(
            {"mymember": Member.objects.get(id=id)}, request
        )
    )


def index(request):
    send_data(request)
    return HttpResponse(loader.get_template("index.html").render())


def testing(request):
    send_data(request)
    return HttpResponse(
        loader.get_template("template.html").render(
            {
                "mymembers": Member.objects.all().values(),
            }
        )
    )


def testsite(request):
    send_data(request)
    return HttpResponse(
        loader.get_template("testsite.html").render(
            {"mymember": Member.objects.all().values()}, request
        )
    )


def pccomps(request):
    send_data(request)
    return HttpResponse(
        loader.get_template("pccomp.html").render(
            {"components": PcComp.objects.all().values()}, request
        )
    )


def partdetails(request, id):
    send_data(request)
    return HttpResponse(
        loader.get_template("partdetails.html").render(
            {"component": PcComp.objects.get(id=id)}, request
        )
    )


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
        task_id = request.session.get("current_task_id")
        if task_id:
            if AsyncResult(task_id).ready():
                del request.session["current_task_id"]
                task_id = None
        if request.method == "POST":
            if request.POST.get("action") == "delete":
                if task_id:
                    current_app.control.revoke(task_id, terminate=True, signal="KILL")
                    task_id = None
                return redirect("time_function")
            else:
                if not task_id:
                    task = timer.delay(
                        int(request.POST.get("time_left", 1)), user_id=request.user.id
                    )
                    task_id = task.id
                    request.session["current_task_id"] = task_id
                    return redirect("time_function")
        return render(request, "timer.html", {"task_id": task_id or 0})
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
        start_time = 0
        for task_id, task_data in (
            requests.get("http://flower:5555/api/tasks", timeout=2).json().items()
        ):
            if ast.literal_eval(task_data["kwargs"])["user_id"] == request.user.id:
                task_data["uuid"] = task_id
                start_time = time.ctime(task_data["started"])
                user_tasks.append(task_data)
        return render(
            request, "output_site.html", {"tasks": user_tasks, "start_time": start_time}
        )
    else:
        return render(request, "access_denied.html")


def task_details(request, uuid):
    send_data(request)
    if request.user.is_authenticated:
        item = requests.get(
            f"http://flower:5555/api/task/info/{uuid}", timeout=2
        ).json()
        if ast.literal_eval(item["kwargs"])["user_id"] == request.user.id:
            return render(
                request,
                "task_details.html",
                {"task": item},
            )
        else:
            return render(request, "access_denied.html")
    else:
        return render(request, "access_denied.html")
