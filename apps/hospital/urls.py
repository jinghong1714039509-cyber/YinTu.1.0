from django.urls import path
from . import views

# 命名空间，对应模板中的 'hospital:xxx'
app_name = 'hospital'

urlpatterns = [
    # 列表页
    # 对应模板: {% url 'hospital:index' %}
    path('', views.index, name='index'),

    # 新建任务页
    # 对应模板: {% url 'hospital:add' %}
    # 原报错行: views.create_dataset_task -> 改为 views.add_task
    path('add/', views.add_task, name='add'),
     # ✅ [新增] 审核工作台
    path('audit/<int:task_id>/', views.audit_workspace, name='audit'),
    # ✅ [新增] 审核提交API
    path('api/audit/save/', views.save_audit_result, name='audit_save'),

]