# config.settings
import os
from pathlib import Path

# 1. 基础路径定义
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. 安全密钥 (生产环境请修改)
SECRET_KEY = 'django-insecure-medical-label-system-core-key'

# 3. 调试模式 (开发时设为 True)
DEBUG = True

ALLOWED_HOSTS = ["*"]

# 4. 已安装的应用 (这里定义了我们的新框架)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # === 我们自定义的模块 ===
    'apps.core',     # 核心数据模型 (对应旧项目的 app/models.py)
    'apps.hospital', # A端业务 (对应旧项目的 LabelTaskView.py)
    'apps.labeler',  # B端业务 (对应旧项目的 LabelTkSampleView.py)
    'apps.users',    # 用户管理 (对应旧项目的 UserView.py)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware', # 初学者建议暂时注释，避免跨域报错
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.DisableBrowserCacheMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # 指向根目录的 templates 文件夹
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# 5. 数据库配置 (这里填您的 MySQL 密码)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "USER": "root",
        "PASSWORD": "eent@123456", # 您的密码
        "HOST": "127.0.0.1",
        "PORT": 3306,
        "NAME": "yintu",      # 建议去 MySQL 新建一个库叫 xcnvs_new
    }
}

# 6. 国际化与时区
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = False # 使用本地时间，方便管理

# 7. 静态文件 (CSS/JS)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# 8. 上传文件 (视频/图片)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 9. 其他配置
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/users/login/'
AUTH_USER_MODEL = 'users.UserProfile'