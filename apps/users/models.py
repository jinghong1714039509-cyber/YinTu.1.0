from django.db import models
from django.contrib.auth.models import AbstractUser

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
    
    # === 【新增】预留扩展字段 ===
    phone = models.CharField(max_length=20, verbose_name='联系电话', null=True, blank=True)
    department = models.CharField(max_length=50, verbose_name='所属科室', null=True, blank=True)
    notes = models.TextField(verbose_name='备注信息', null=True, blank=True)
    
    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name
        db_table = 'user_profile'