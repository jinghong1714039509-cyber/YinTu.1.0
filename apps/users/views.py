# apps/users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm


def login_view(request):
    # 如果已经登录，直接根据身份跳转
    if request.user.is_authenticated:
        return redirect_based_on_role(request.user)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"欢迎回来，{user.username}！")
            return redirect_based_on_role(user)
        else:
            messages.error(request, "账号或密码错误")
    
    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    return redirect('users:login')

def redirect_based_on_role(user):
    """根据用户角色决定跳转到哪里"""
    if user.is_superuser:
        # 管理员默认去 A 端，也可以去后台
        return redirect('hospital:index')
    elif user.role == 'hospital':
        return redirect('hospital:index')
    elif user.role == 'labeler':
        return redirect('labeler:dashboard')
    else:
        return redirect('users:login')
def register_view(request):
    """用户注册"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # 1. 保存新用户
            user = form.save()
            
            # 2. 注册完成后直接登录
            login(request, user)
            
            # 3. 发送欢迎消息并跳转
            messages.success(request, f"注册成功！欢迎您，{user.username}")
            return redirect_based_on_role(user)
        else:
            # 如果校验失败（比如用户名已存在、两次密码不一致），把错误传给模板
            # form.errors 会包含具体的错误信息
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return render(request, 'users/register.html')