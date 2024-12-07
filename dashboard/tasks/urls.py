from django.urls import path
from . import views

urlpatterns = [path('', views.task_dashboard, name='task_dashboard')]