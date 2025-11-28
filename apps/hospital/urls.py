# apps.hospital.urls
from django.urls import path
from . import views

app_name = 'hospital'

urlpatterns = [
    path('', views.index, name='index'),      # 列表页
    path('add/', views.add_task, name='add'), # 添加页
]