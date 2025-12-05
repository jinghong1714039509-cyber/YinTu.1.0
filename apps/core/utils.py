# apps/core/utils.py
import os
import random
import string
import time
from cryptography.fernet import Fernet
from django.conf import settings
# 动态引入模型，防止循环引用
from django.apps import apps

# 生成随机编号 (如 TK20231130...)
def gen_random_code(prefix="TK", length=4):
    timestamp = time.strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}{timestamp}{random_str}"

# 获取加密密钥 (单例模式)
def get_cipher_suite():
    key_path = os.path.join(settings.BASE_DIR, 'secret.key')
    if not os.path.exists(key_path):
        key = Fernet.generate_key()
        with open(key_path, "wb") as key_file:
            key_file.write(key)
    else:
        with open(key_path, "rb") as key_file:
            key = key_file.read()
    return Fernet(key)

# 加密文件内容
def encrypt_file(file_data):
    cipher = get_cipher_suite()
    return cipher.encrypt(file_data)

# 简单的分页页码生成器
def build_page_labels(current_page, total_pages):
    return [{"page": i, "cur": 1 if i == current_page else 0, "name": str(i)} for i in range(1, total_pages + 1)]

# ✅ [新增] 获取客户端 IP
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# ✅ [新增] 通用日志记录函数
def log_operation(request, action, target, details=""):
    """
    全站通用的日志记录入口
    """
    if request.user.is_authenticated:
        # 动态获取模型，避免循环导入 user.models
        try:
            OperationLog = apps.get_model('users', 'OperationLog')
            OperationLog.objects.create(
                operator=request.user,
                action=action,
                target=target,
                details=details,
                ip_address=get_client_ip(request)
            )
        except Exception as e:
            print(f"日志记录失败: {e}")