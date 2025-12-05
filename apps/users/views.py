from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
# ✅ 新增：分页和复杂查询工具
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

# ✅ 新增：引入日志模型
from .models import OperationLog

# 尝试引入自定义表单
try:
    from .forms import RegisterForm
except ImportError:
    from django.contrib.auth.forms import UserCreationForm as RegisterForm

User = get_user_model()

# ==========================================
#  辅助函数
# ==========================================
def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# ==========================================
#  普通用户功能
# ==========================================

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
                return redirect('users:manage_list') 
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

@login_required
def change_password_view(request):
    """用户自行修改密码"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) 
            messages.success(request, "密码修改成功！")
            
            if user.is_superuser: return redirect('users:manage_list')
            if user.role == 'labeler': return redirect('labeler:dashboard')
            return redirect('hospital:index')
        else:
            messages.error(request, "请修正下面的错误")
    else:
        form = PasswordChangeForm(request.user)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
            
    return render(request, 'users/change_password.html', {'form': form})

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
    target_name = target_user.username  # 记录名字
    
    if target_user.is_superuser:
        messages.error(request, "不能删除超级管理员！")
    else:
        target_user.delete()
        
        # ✅ 记录日志
        OperationLog.objects.create(
            operator=request.user,
            action="删除用户",
            target=target_name,
            details=f"管理员删除了用户ID: {user_id}",
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, f"用户 {target_name} 已删除")
    return redirect('users:manage_list')

@login_required
@user_passes_test(is_superuser)
def user_reset_password(request, user_id):
    """重置密码"""
    target_user = get_object_or_404(User, id=user_id)
    target_user.set_password("123456")
    target_user.save()
    
    # ✅ 记录日志
    OperationLog.objects.create(
        operator=request.user,
        action="重置密码",
        target=target_user.username,
        details="管理员将密码重置为默认: 123456",
        ip_address=get_client_ip(request)
    )
    
    messages.success(request, f"用户 {target_user.username} 的密码已重置为 '123456'")
    return redirect('users:manage_list')

@login_required
@user_passes_test(is_superuser)
def operation_log_list(request):
    """
    ✅ [新增] 操作日志审计页面 (带服务端分页与搜索)
    """
    search_query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    
    # 1. 基础查询 (优化查询性能)
    logs_qs = OperationLog.objects.select_related('operator').all().order_by('-create_time')
    
    # 2. 搜索过滤
    if search_query:
        logs_qs = logs_qs.filter(
            Q(operator__username__icontains=search_query) |
            Q(action__icontains=search_query) |
            Q(target__icontains=search_query) |
            Q(ip_address__icontains=search_query)
        )
    
    # 3. 分页处理 (每页 20 条)
    paginator = Paginator(logs_qs, 20)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
        
    context = {
        'page_obj': page_obj,      # 当前页对象
        'search_query': search_query, # 回填搜索框
    }
    return render(request, 'users/log_list.html', context)