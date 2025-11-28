import os

# 定义新的目录结构
structure = {
    "config": ["__init__.py", "settings.py", "urls.py", "wsgi.py"],
    "apps": ["__init__.py"],
    "apps/core": ["__init__.py", "models.py", "utils.py", "admin.py"],
    "apps/users": ["__init__.py", "views.py", "urls.py"],
    "apps/hospital": ["__init__.py", "views.py", "urls.py"],  # A端
    "apps/labeler": ["__init__.py", "views.py", "urls.py"],  # B端
    "static": [],
    "static/css": [],
    "static/js": [],
    "static/images": [],
    "templates": [],
    "templates/common": ["base.html", "index.html", "login.html"],  # 公共模板
    "templates/hospital": ["add_task.html", "task_list.html"],  # A端模板
    "templates/labeler": ["workspace.html"],  # B端模板
    "media": [],  # 用于存放上传的文件
    "media/secure_data": [],  # 加密数据
    "media/video_source": [],  # 原始视频
    "logs": [],
}


def create_project():
    base_dir = os.getcwd()
    print(f"🚀 开始在 {base_dir} 构建新框架...")

    # 1. 创建目录和文件
    for folder, files in structure.items():
        folder_path = os.path.join(base_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"   [创建目录] {folder}")

        for file in files:
            file_path = os.path.join(folder_path, file)
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    # 写入一些基础注释
                    if file.endswith('.py'):
                        f.write(f"# {folder.replace('/', '.')}.{file.replace('.py', '')}\n")
                print(f"   [创建文件] {file}")

    # 2. 生成 manage.py (Django 的入口)
    manage_py_content = """#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
"""
    with open(os.path.join(base_dir, 'manage.py'), 'w', encoding='utf-8') as f:
        f.write(manage_py_content)
    print("   [生成入口] manage.py")

    # 3. 生成 .gitignore (解决您上传 GitHub 太大的问题)
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
venv/
env/

# Django
*.log
db.sqlite3
media/
static/staticfiles/

# System
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Sensitive Keys
secret.key
"""
    with open(os.path.join(base_dir, '.gitignore'), 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print("   [安全配置] .gitignore")

    print("\n✅ 框架构建完成！请按照下一步指示填充配置。")


if __name__ == '__main__':
    create_project()