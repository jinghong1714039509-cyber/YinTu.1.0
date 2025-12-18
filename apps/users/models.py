from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class UserProfile(AbstractUser):
    """
    自定义用户表：增加了身份、电话、科室、备注等扩展字段
    """
    ROLE_CHOICES = (
        ('hospital', '医院医生'),
        ('labeler', '标注员'),
    )
    
    # 核心身份字段
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='labeler', verbose_name='身份')
    
    # 预留扩展字段
    phone = models.CharField(max_length=20, verbose_name='联系电话', null=True, blank=True)
    department = models.CharField(max_length=50, verbose_name='所属科室', null=True, blank=True)
    notes = models.TextField(verbose_name='备注信息', null=True, blank=True)
    
    # 用户头像字段
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/', 
        default='images/user.png', 
        verbose_name='用户头像',
        null=True, blank=True
    )

    # ✅ [新增] 动态获取角色头像的方法
    def get_role_avatar(self):
        """
        根据角色获取头像链接：
        1. 如果用户自己上传了新头像（且不是默认图），使用上传的。
        2. 否则，根据身份返回对应的卡通图标。
        """
        # 判断是否有自定义上传 (排除掉数据库默认的字符串)
        if self.avatar and str(self.avatar) != 'images/user.png':
             return self.avatar.url
        
        # 根据角色返回静态文件路径
        base_path = '/static/images/'
        if self.is_superuser:
            return base_path + 'avatar_admin.png'   # 管理员图标
        elif self.role == 'hospital':
            return base_path + 'avatar_doctor.png'  # 医生图标
        else:
            return base_path + 'avatar_labeler.png' # 标注员图标
    
    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name
        db_table = 'user_profile'

class OperationLog(models.Model):
    """
    系统操作日志
    """
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='操作人')
    action = models.CharField(max_length=50, verbose_name='动作类型')
    target = models.CharField(max_length=100, verbose_name='操作对象', null=True, blank=True)
    ip_address = models.GenericIPAddressField(verbose_name='IP地址', null=True, blank=True)
    details = models.TextField(verbose_name='详细信息', null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        verbose_name = '操作日志'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']
        db_table = 'operation_log'