import json
import datetime
# 1. 引入系统监控库 (防止报错)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.db.models.functions import TruncDate
from django.utils import timezone

# 引入核心模型
from apps.core.models import (
    LabelTask, SampleImage, 
    STATUS_PROCESSING, STATUS_DONE, STATUS_REVIEWING, STATUS_REJECTED, STATUS_ERROR
)

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
            if user.is_superuser:
                return redirect('users:admin_dashboard') 
            elif getattr(user, 'role', '') == 'labeler':
                return redirect('labeler:dashboard')
            elif getattr(user, 'role', '') == 'hospital':
                return redirect('hospital:index')
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
            
            if user.is_superuser: return redirect('users:admin_dashboard')
            if getattr(user, 'role', '') == 'labeler': return redirect('labeler:dashboard')
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
    """
    用户管理列表 (带服务端分页与搜索)
    ✅ [修改] 增加了账号统计数据的计算
    """
    search_query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    
    # 1. 基础查询
    users_qs = User.objects.all().order_by('-date_joined')
    
    # 2. 搜索过滤
    if search_query:
        users_qs = users_qs.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # 3. 分页处理 (每页 15 条)
    paginator = Paginator(users_qs, 15)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # 4. ✅ [新增] 统计数据逻辑
    # 统计各角色人数，用于前端展示
    total_users = User.objects.count()
    admin_count = User.objects.filter(is_superuser=True).count()
    # 假设 role 字段存在 ('hospital' 为医生, 'labeler' 为标注员)
    doctor_count = User.objects.filter(role='hospital').count()
    labeler_count = User.objects.filter(role='labeler').count()
    
    stats = {
        'total': total_users,
        'admins': admin_count,
        'doctors': doctor_count,
        'labelers': labeler_count,
        # 这里的 'others' 是未分配角色的用户
        'others': total_users - (admin_count + doctor_count + labeler_count)
    }
        
    context = {
        'page_obj': page_obj,          
        'search_query': search_query, 
        'total_count': users_qs.count(),
        'stats': stats  # ✅ 将统计数据传递给模板
    }
    return render(request, 'users/manage_list.html', context)

@login_required
@user_passes_test(is_superuser)
def user_delete(request, user_id):
    """删除用户"""
    target_user = get_object_or_404(User, id=user_id)
    target_name = target_user.username 
    
    if target_user.is_superuser:
        messages.error(request, "不能删除超级管理员！")
    else:
        target_user.delete()
        
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
    操作日志审计页面 (带服务端分页与搜索)
    """
    search_query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    
    logs_qs = OperationLog.objects.select_related('operator').all().order_by('-create_time')
    
    if search_query:
        logs_qs = logs_qs.filter(
            Q(operator__username__icontains=search_query) |
            Q(action__icontains=search_query) |
            Q(target__icontains=search_query) |
            Q(ip_address__icontains=search_query)
        )
    
    paginator = Paginator(logs_qs, 20)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
        
    context = {
        'page_obj': page_obj,      
        'search_query': search_query, 
    }
    return render(request, 'users/log_list.html', context)

@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    """
    [超级管理员] 全景数据驾驶舱
    """
    # 1. 服务器状态
    if HAS_PSUTIL:
        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            server_stats = {
                'cpu': cpu_usage,
                'memory': int(memory.percent),
                'disk': int(disk.percent),
                'disk_used_gb': round(disk.used / (1024**3), 1),
                'disk_total_gb': round(disk.total / (1024**3), 1),
            }
        except Exception:
            server_stats = {'cpu': 0, 'memory': 0, 'disk': 0, 'disk_used_gb': 0, 'disk_total_gb': 0}
    else:
        server_stats = {'cpu': 0, 'memory': 0, 'disk': 0, 'disk_used_gb': 0, 'disk_total_gb': 0}

    # 2. 在线人数
    time_threshold = timezone.now() - datetime.timedelta(minutes=30)
    active_users = User.objects.filter(last_login__gte=time_threshold)
    
    online_stats = {
        'total': active_users.count(),
        'doctors': active_users.filter(role='hospital').count(),
        'labelers': active_users.filter(role='labeler').count(),
        'admins': active_users.filter(is_superuser=True).count()
    }

    # 3. 任务状态分布
    task_counts = LabelTask.objects.aggregate(
        processing=Count('id', filter=Q(state=STATUS_PROCESSING)),
        done=Count('id', filter=Q(state=STATUS_DONE)),
        reviewing=Count('id', filter=Q(state=STATUS_REVIEWING)),
        rejected=Count('id', filter=Q(state=STATUS_REJECTED)),
        error=Count('id', filter=Q(state=STATUS_ERROR))
    )
    
    pie_data = [
        {'value': task_counts['processing'] or 0, 'name': '处理中'},
        {'value': task_counts['done'] or 0, 'name': '已完成'},
        {'value': task_counts['reviewing'] or 0, 'name': '待审核'},
        {'value': task_counts['rejected'] or 0, 'name': '被驳回'},
        {'value': task_counts['error'] or 0, 'name': '异常'},
    ]

    # 4. 趋势图
    today = timezone.now().date()
    seven_days_ago = today - datetime.timedelta(days=6)
    
    daily_tasks = LabelTask.objects.filter(created_at__date__gte=seven_days_ago)\
        .annotate(date=TruncDate('created_at'))\
        .values('date')\
        .annotate(count=Count('id'))\
        .order_by('date')
        
    date_map = { (seven_days_ago + datetime.timedelta(days=i)): 0 for i in range(7) }
    for item in daily_tasks:
        if item['date'] in date_map:
            date_map[item['date']] = item['count']
            
    trend_labels = [d.strftime('%m-%d') for d in sorted(date_map.keys())]
    trend_data = [date_map[d] for d in sorted(date_map.keys())]

    # 5. 标注员真实排行榜
    labeler_stats = SampleImage.objects.filter(is_labeled=True)\
        .exclude(labeled_by__isnull=True)\
        .exclude(labeled_by='')\
        .values('labeled_by')\
        .annotate(total_count=Count('id'))\
        .order_by('-total_count')[:5]

    top_labelers = []
    for stat in labeler_stats:
        username = stat['labeled_by']
        user_obj = User.objects.filter(username=username).first()
        role_display = '标注员'
        if user_obj:
            if user_obj.is_superuser:
                role_display = '管理员'
            else:
                role_display = dict(User.ROLE_CHOICES).get(user_obj.role, '标注员')

        top_labelers.append({
            'name': username,
            'role': role_display,
            'count': stat['total_count'],
            'accuracy': 100 
        })

    context = {
        'server_stats': json.dumps(server_stats),
        'online_stats': json.dumps(online_stats),
        'pie_data': json.dumps(pie_data),
        'trend_labels': json.dumps(trend_labels),
        'trend_data': json.dumps(trend_data),
        'top_labelers': json.dumps(top_labelers),
        'currentTime': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return render(request, 'users/admin_dashboard.html', context)