# config.wsgi
import os
from django.core.wsgi import get_wsgi_application

# 告诉 Django 使用哪个配置文件
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 创建应用实例 (这就是报错说找不到的 application)
application = get_wsgi_application()