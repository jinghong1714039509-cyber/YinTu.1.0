from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
# ✅ 关键修复：必须引入 login_required 和 user_passes_test
from django.contrib.auth.decorators import login_required, user_passes_test

# 尝试引入您自定义的注册表单
try:
    from .forms import RegisterForm
except ImportError:
    # 如果没有自定义表单，为了防止报错，回退到系统默认
    from django.contrib.auth.forms import UserCreationForm as RegisterForm

User = get_user_model()

def login_view(request):
    """用户登录"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # 登录成功后，根据角色智能跳转
            if getattr(user, 'role', '') == 'labeler':
                return redirect('labeler:dashboard')
            elif getattr(user, 'role', '') == 'hospital':
                return redirect('hospital:index')
            elif user.is_superuser:
                return redirect('/admin/') # 或者去用户管理页 users:manage_list
            else:
                return redirect('/')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    """用户注销"""
    logout(request)
    return redirect('users:login')

def register_view(request):
    """用户注册"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "注册成功，请登录")
            return redirect('users:login')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})

# ==========================================
#  超级管理员功能
# ==========================================

def is_superuser(user):
    """权限检查：是否为超级管理员"""
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def user_manage_list(request):
    """用户管理列表"""
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'users/manage_list.html', {'users': users})

@login_required
@user_passes_test(is_superuser)
def user_delete(request, user_id):
    """删除用户"""
    target_user = get_object_or_404(User, id=user_id)
    if target_user.is_superuser:
        messages.error(request, "不能删除超级管理员！")
    else:
        target_user.delete()
        messages.success(request, f"用户 {target_user.username} 已删除")
    return redirect('users:manage_list')

@login_required
@user_passes_test(is_superuser)
def user_reset_password(request, user_id):
    """重置密码"""
    target_user = get_object_or_404(User, id=user_id)
    # 重置为固定密码，方便管理，您也可以改为随机生成
    target_user.set_password("123456")
    target_user.save()
    messages.success(request, f"用户 {target_user.username} 的密码已重置为 '123456'")
    return redirect('users:manage_list')