from django.db import models
from django.contrib.auth.models import AbstractUser

class UserProfile(AbstractUser):
    """
    自定义用户表：增加了 role 身份字段
    """
    ROLE_CHOICES = (
        ('hospital', '医院医生'),
        ('labeler', '标注员'),
    )
    # 默认为标注员
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='labeler', verbose_name='身份')
    
    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name
        db_table = 'user_profile' # 自定义表名