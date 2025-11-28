# config.urls
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

# 简单的首页重定向
def home_redirect(request):
    # 如果未登录，去登录
    # if not request.user.is_authenticated:
    #     return redirect('/users/login/')
    # 暂时先跳到 A 端测试，后续我们做个大首页
    return redirect('/hospital/add/')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 首页
    path('', home_redirect),
    
    # 分发到各个子模块
    # path('users/', include('apps.users.urls')),
    path('hospital/', include('apps.hospital.urls')), # A端路由
    # path('labeler/', include('apps.labeler.urls')), # B端路由
]

# 开发模式下，让 Django 可以直接访问上传的图片/视频
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])