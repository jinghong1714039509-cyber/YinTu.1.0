from django.urls import path
from . import views

app_name = 'hospital'

urlpatterns = [
    # ✅ 新增这一行：处理 /hospital/ 根路径，默认显示列表页
    path('', views.index, name='home'),

    # A端新建任务
    path('add/', views.add_task, name='add'),
    
    # A端任务列表
    path('index/', views.index, name='index'), 
]