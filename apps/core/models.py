# apps/core/models.py
from django.db import models
from django.conf import settings  # <--- 改动1: 引入配置

# 状态常量
STATUS_PROCESSING = 0
STATUS_READY = 1
STATUS_DONE = 2
STATUS_ERROR = 9

class LabelTask(models.Model):
    """
    [A端核心表] 任务与病例
    """
    # 基础信息
    code = models.CharField(max_length=50, verbose_name='任务编号', unique=True)
    name = models.CharField(max_length=100, verbose_name='任务/患者名称')
    remark = models.TextField(verbose_name='病情备注', null=True, blank=True)
    
    # 归属 (关联到系统用户表)
    # <--- 改动2: 这里不再写 User，而是写 settings.AUTH_USER_MODEL
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='创建医生')
    
    # === A端上传的核心文件 ===
    patient_file_path = models.CharField(max_length=500, verbose_name='加密病例路径', null=True, blank=True)
    source_video_path = models.CharField(max_length=500, verbose_name='原始视频路径', null=True, blank=True)
    
    # 处理设置
    video_fps = models.IntegerField(default=30, verbose_name='抽帧频率')
    
    # 状态与统计
    sample_count = models.IntegerField(default=0, verbose_name='样本数量')
    labeled_count = models.IntegerField(default=0, verbose_name='已标注数')
    state = models.IntegerField(default=STATUS_PROCESSING, verbose_name='状态') 
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'core_label_task'
        verbose_name = '病例任务'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

class SampleImage(models.Model):
    """
    [B端核心表] 样本图片
    """
    task = models.ForeignKey(LabelTask, on_delete=models.CASCADE, related_name='samples')
    code = models.CharField(max_length=50, verbose_name='样本编号')
    file_path = models.CharField(max_length=500, verbose_name='图片路径')
    original_name = models.CharField(max_length=200, verbose_name='文件名')
    
    is_labeled = models.BooleanField(default=False, verbose_name='是否已标注')
    annotation_content = models.TextField(verbose_name='标注数据(XML/JSON)', null=True, blank=True)
    
    labeled_by = models.CharField(max_length=100, verbose_name='标注员', null=True, blank=True)
    labeled_at = models.DateTimeField(null=True, blank=True, verbose_name='标注时间')

    class Meta:
        db_table = 'core_sample_image'
        verbose_name = '样本图片'