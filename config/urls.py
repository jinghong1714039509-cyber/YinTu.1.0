# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def home_redirect(request):
    # 首页直接跳到 A 端新建任务页
    return redirect('/hospital/add/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect),
    
    # A端路由
    path('hospital/', include('apps.hospital.urls')), 
    
    # B端路由 (取消注释)
    path('labeler/', include('apps.labeler.urls')),
]

# 媒体文件访问配置
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])