from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.http import HttpResponse
from django.template import loader
from .models import Member
from .models import PcComp

def members(request):
    mymembers = Member.objects.all().values()
    template = loader.get_template('members.html')
    context = {
        'mymembers' : mymembers,
    }
    return HttpResponse(template.render(context, request))

def details(request, id):
    mymember = Member.objects.get(id=id)
    template = loader.get_template('details.html')
    context = {
        'mymember' : mymember
    }
    return HttpResponse(template.render(context, request))

def index(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render())

def testing(request):
    mymembers = Member.objects.all().values()
    template = loader.get_template('template.html')
    context = {
        'mymembers' : mymembers,
    }
    return HttpResponse(template.render(context, request))

def testsite(request):
    mymember = Member.objects.all().values()
    template = loader.get_template('testsite.html')
    context = {
        'mymember' : mymember
    }
    return HttpResponse(template.render(context, request))

def pccomps(request):
    components = PcComp.objects.all().values()
    template = loader.get_template('pccomp.html')
    context = {
        'components' : components
    }
    return HttpResponse(template.render(context, request))

def partdetails(request, id):
    component = PcComp.objects.get(id=id)
    template = loader.get_template('partdetails.html')
    context = {
        'component' : component
    }
    return HttpResponse(template.render(context, request))

def customfunctions(request):
    template = loader.get_template('customfunctions.html')
    return HttpResponse(template.render())

def addition(request):
    if request.user.is_authenticated:
        num1 = int(request.POST.get('num1', 0))
        num2 = int(request.POST.get('num2', 0))
        x = num1 + num2
        template = loader.get_template('addition.html')
        context = {
            'x' : x
        }
        return HttpResponse(template.render(context, request))
    else:
        return HttpResponse(loader.get_template('access_denied.html').render())

def subtraction(request):
    if request.user.is_authenticated:
        num1 = int(request.POST.get('num1', 0))
        num2 = int(request.POST.get('num2', 0))
        x = num1 - num2
        template = loader.get_template('subtraction.html')
        context = {
            'x' : x
        }
        return HttpResponse(template.render(context, request))
    else:
        return HttpResponse(loader.get_template('access_denied.html').render())

def multiplication(request):
    if request.user.is_authenticated and request.user.has_perm('members.multiplication_access'):
        num1 = int(request.POST.get('num1', 0))
        num2 = int(request.POST.get('num2', 0))
        x = num1 * num2
        template = loader.get_template('multiplication.html')
        context = {
            'x' : x
        }
        return HttpResponse(template.render(context, request))
    else:
        return HttpResponse(loader.get_template('access_denied.html').render())

def login_form(request):
    if request.user.is_authenticated:
        return redirect('index')
    else:
        context = {}
        if request.method == 'POST':
            form = AuthenticationForm(data=request.POST)
            if form.is_valid():
                login(request, form.get_user())
                return redirect('index')
            else:
                context = {
                    'statusCode' : 'Invalid login',
                }
        else:
            form = AuthenticationForm()
        template = loader.get_template('login_form.html')
        return HttpResponse(template.render(context, request))

def logoutsite(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('login_form')
    else:
        return redirect('index')
