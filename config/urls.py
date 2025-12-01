# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def home_redirect(request):
    # 如果没登录，去登录页
    if not request.user.is_authenticated:
        return redirect('users:login')
    # 如果登录了，根据角色跳转 (复用 views 里的逻辑，或者简单跳到 A 端)
    return redirect('hospital:index')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect),
    
    # 注册各个模块
    path('users/', include('apps.users.urls')),  # <--- 确保这行存在
    path('hospital/', include('apps.hospital.urls')),
    path('labeler/', include('apps.labeler.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])