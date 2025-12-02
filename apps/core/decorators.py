from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from functools import wraps

def hospital_required(view_func):
    """
    装饰器：仅允许 role='hospital' 或 超级管理员 访问
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        
        # ✅ 【核心修改】增加 "and not request.user.is_superuser"
        # 意思就是：如果角色不对，且不是超级管理员，才报错。
        if request.user.role != 'hospital' and not request.user.is_superuser:
            raise PermissionDenied("您没有权限访问医生工作台！")
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def labeler_required(view_func):
    """
    装饰器：仅允许 role='labeler' 或 超级管理员 访问
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        
        # ✅ 【核心修改】同样给 B 端也加上超级管理员特权
        if request.user.role != 'labeler' and not request.user.is_superuser:
            raise PermissionDenied("您没有权限访问标注员工作台！")
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view