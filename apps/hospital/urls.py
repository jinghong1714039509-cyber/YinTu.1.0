from django.urls import path
from . import views

app_name = 'hospital'

urlpatterns = [
    # A端新建任务
    path('add/', views.add_task, name='add'),
    
    # A端任务列表 (注意：根据您的 views.py，这里函数名可能是 index 或 task_list)
    # 如果您之前的 views.py 里叫 def index(request)，就用 views.index
    path('index/', views.index, name='index'), 
]