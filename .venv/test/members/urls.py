from django.urls import path
from . import views

urlpatterns = [
    path('members/', views.members, name='members'),
    path('members/details/<int:id>', views.details, name='details'),
    path('', views.index, name='index'),
    path('testsite/', views.testsite, name='testsite'),
    path('pccomp/', views.pccomps, name='pccomp'),
    path('pccomp/partdetails/<int:id>', views.partdetails, name='partdetails'),
    path('customfunctions/', views.customfunctions, name='customfunctions'),
    path('customfunctions/addition/', views.addition, name='addition'),
    path('customfunctions/subtraction/', views.subtraction, name='subtraction'),
    path('customfunctions/multiplication/', views.multiplication, name='multiplication'),
    path('login_form/', views.login_form, name='login_form'),
    path('logoutsite/', views.logoutsite, name='logoutsite')
]