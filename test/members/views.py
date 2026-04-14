from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader

from .models import Member, PcComp
from .signals import custom_signal


def send_data(request):
    custom_signal.send(
        sender=None, user=request.user, information=(request, request.GET, request.POST)
    )


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
    if request.user.is_authenticated:
        num1 = int(request.POST.get("num1", 0))
        num2 = int(request.POST.get("num2", 0))
        if isinstance(num1, int) and isinstance(num2, int):
            x = num1 + num2
            send_data(request)
            return HttpResponse(
                loader.get_template("addition.html").render({"x": x}, request)
            )
    else:
        send_data(request)
        return HttpResponse(loader.get_template("access_denied.html").render())


def subtraction(request):
    if request.user.is_authenticated:
        num1 = int(request.POST.get("num1", 0))
        num2 = int(request.POST.get("num2", 0))
        if isinstance(num1, int) and isinstance(num2, int):
            x = num1 - num2
            send_data(request)
            return HttpResponse(
                loader.get_template("subtraction.html").render({"x": x}, request)
            )
    else:
        send_data(request)
        return HttpResponse(loader.get_template("access_denied.html").render())


def multiplication(request):
    if request.user.is_authenticated and request.user.has_perm(
        "members.multiplication_access"
    ):
        num1 = int(request.POST.get("num1", 0))
        num2 = int(request.POST.get("num2", 0))
        if isinstance(num1, int) and isinstance(num2, int):
            x = num1 * num2
            send_data(request)
            return HttpResponse(
                loader.get_template("multiplication.html").render({"x": x}, request)
            )
    else:
        send_data(request)
        return HttpResponse(loader.get_template("access_denied.html").render())


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
