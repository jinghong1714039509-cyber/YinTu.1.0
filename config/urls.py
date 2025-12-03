# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def home_redirect(request):
    """
    智能首页路由：根据登录状态和用户角色自动分流
    """
    # 1. 未登录 -> 跳转登录页
    if not request.user.is_authenticated:
        return redirect('users:login')
    
    # 2. 已登录 -> 获取用户角色 (role)
    # 使用 getattr 防止 User 模型没 role 字段时报错
    user_role = getattr(request.user, 'role', None)

    # 3. 根据角色分流
    if user_role == 'labeler':
        # 标注员 -> B端工作台 (我们刚做好的卡片页)
        return redirect('labeler:dashboard')
    elif user_role == 'hospital':
        # 医生 -> A端任务列表
        return redirect('hospital:index')
    
    # 4. 管理员或其他未知角色 -> 默认去医院端或 Admin
    if request.user.is_superuser:
        return redirect('/admin/')
        
    return redirect('hospital:index')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 给首页加上 name='home'，方便模板中引用
    path('', home_redirect, name='home'),
    
    # === 注册各个应用模块 ===
    path('users/', include('apps.users.urls')),      # 用户认证
    path('hospital/', include('apps.hospital.urls')), # A端：医生/医院
    path('labeler/', include('apps.labeler.urls')),   # B端：标注/执行
]

# === 开发环境配置 (DEBUG=True) ===
if settings.DEBUG:
    # 1. 关键：配置媒体文件 (Media) 服务
    # 只有加上这就话，前端 <img src="/media/..."> 才能正常显示图片！
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # 2. 配置静态文件 (Static)
    # Django runserver 通常会自动处理 static，但如果您的静态文件没加载出来，可以保留下面这行。
    # 增加了安全判断，防止 STATICFILES_DIRS 为空时报错。
    if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])