# apps.core.utils
import os
import random
import string
import time
from cryptography.fernet import Fernet
from django.conf import settings

# --- 1. 随机码生成器 ---
def gen_random_code(prefix="", length=4):
    """
    生成唯一编号，例如: TK20231128xxxx
    """
    timestamp = time.strftime('%Y%m%d%H%M%S', time.localtime())
    random_str = ''.join(random.sample(string.ascii_letters + string.digits, length))
    return f"{prefix}{timestamp}{random_str}"

# --- 2. 加密工具 ---
# 密钥文件路径
KEY_FILE = os.path.join(settings.BASE_DIR, "secret.key")

def get_cipher_suite():
    """
    获取或生成加密套件
    """
    if not os.path.exists(KEY_FILE):
        # 如果没有密钥，生成一个并保存
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
    else:
        # 读取现有密钥
        with open(KEY_FILE, "rb") as key_file:
            key = key_file.read()
    return Fernet(key)

def encrypt_file(file_data):
    """
    加密文件内容
    :param file_data: 二进制文件内容
    :return: 加密后的二进制内容
    """
    cipher = get_cipher_suite()
    return cipher.encrypt(file_data)

def decrypt_file(encrypted_data):
    """
    解密文件内容
    """
    cipher = get_cipher_suite()
    return cipher.decrypt(encrypted_data)