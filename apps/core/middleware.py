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