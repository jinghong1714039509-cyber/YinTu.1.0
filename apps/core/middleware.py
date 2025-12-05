from django.core.cache import cache
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class DisableBrowserCacheMiddleware(MiddlewareMixin):
    """
    禁止浏览器缓存中间件
    在响应头中添加禁止缓存的指令，防止用户登出后点击后退按钮看到敏感页面
    """
    def process_response(self, request, response):
        # 仅针对已登录用户的请求，或者是所有请求（视您的安全性要求而定）
        # 这里建议对所有请求都加，或者至少对非静态文件请求加
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response

class ActiveUserMiddleware(MiddlewareMixin):
    """
    实时在线用户中间件
    记录用户最后一次访问的时间，有效期设为5分钟（300秒）
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            now = timezone.now()
            # 缓存键：online_user_用户ID
            cache.set(f'online_user_{request.user.id}', now, 300)