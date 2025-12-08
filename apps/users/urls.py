from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('register/', views.register_view, name='register'), 
    path('manage/', views.user_manage_list, name='manage_list'),
    path('manage/delete/<int:user_id>/', views.user_delete, name='user_delete'),
    path('manage/reset/<int:user_id>/', views.user_reset_password, name='user_reset'),
    path('logs/', views.operation_log_list, name='log_list'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
]