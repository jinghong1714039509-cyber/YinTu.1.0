from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile

class UserProfileAdmin(UserAdmin):
    # 在用户详情页添加 'role' 字段的编辑框
    fieldsets = UserAdmin.fieldsets + (
        ('身份设置', {'fields': ('role',)}),
    )
    # 在用户列表页显示 'role'
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')

admin.site.register(UserProfile, UserProfileAdmin)