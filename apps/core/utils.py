# apps/core/utils.py
import os
import random
import string
import time
from cryptography.fernet import Fernet
from django.conf import settings

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

# 简单的分页页码生成器 (对应旧项目的 buildPageLabels)
def build_page_labels(current_page, total_pages):
    # 简单实现：返回 [1, 2, 3, ...]
    return [{"page": i, "cur": 1 if i == current_page else 0, "name": str(i)} for i in range(1, total_pages + 1)]