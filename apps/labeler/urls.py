from django.urls import path
from . import views

app_name = 'labeler'

urlpatterns = [
    # B端首页 (看板)
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # 图片墙
    path('gallery/<int:task_id>/', views.gallery, name='gallery'),
    
    # 下载
    path('download/<int:task_id>/', views.download_zip, name='download'),
    
    # 上传
    path('upload/<int:task_id>/', views.upload_annotation, name='upload'),
]