# apps.core.models
from django.db import models
from django.contrib.auth.models import User

# 状态常量
STATUS_PROCESSING = 0
STATUS_READY = 1
STATUS_DONE = 2
STATUS_ERROR = 9

class LabelTask(models.Model):
    """
    [A端核心表] 任务与病例
    对应旧代码: LabelTaskModel
    """
    # 基础信息
    code = models.CharField(max_length=50, verbose_name='任务编号', unique=True)
    name = models.CharField(max_length=100, verbose_name='任务/患者名称')
    remark = models.TextField(verbose_name='病情备注', null=True, blank=True)
    
    # 归属 (关联到系统用户表)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建医生')
    
    # === A端上传的核心文件 ===
    # 1. 加密后的病例文件路径 (例如: media/secure/enc_data.bin)
    patient_file_path = models.CharField(max_length=500, verbose_name='加密病例路径', null=True, blank=True)
    
    # 2. 原始视频路径 (例如: media/video/source.mp4)
    # 注意：这个路径不对B端公开
    source_video_path = models.CharField(max_length=500, verbose_name='原始视频路径', null=True, blank=True)
    
    # 处理设置
    video_fps = models.IntegerField(default=30, verbose_name='抽帧频率')
    
    # 状态与统计
    sample_count = models.IntegerField(default=0, verbose_name='样本数量')
    labeled_count = models.IntegerField(default=0, verbose_name='已标注数')
    state = models.IntegerField(default=STATUS_PROCESSING, verbose_name='状态') # 0:处理中 1:就绪
    
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
    对应旧代码: LabelTkSampleModel
    B端只能看到这张表里的图片，看不到上面的视频
    """
    # 关联任务
    task = models.ForeignKey(LabelTask, on_delete=models.CASCADE, related_name='samples')
    
    # 图片信息
    code = models.CharField(max_length=50, verbose_name='样本编号')
    
    # B端访问的相对路径 (例如: upload/images/TK001/1.jpg)
    file_path = models.CharField(max_length=500, verbose_name='图片路径')
    
    # 原始文件名 (例如: img_0001.jpg)
    original_name = models.CharField(max_length=200, verbose_name='文件名')
    
    # 标注结果
    is_labeled = models.BooleanField(default=False, verbose_name='是否已标注')
    annotation_content = models.TextField(verbose_name='标注数据(XML/JSON)', null=True, blank=True)
    
    labeled_by = models.CharField(max_length=100, verbose_name='标注员', null=True, blank=True)
    labeled_at = models.DateTimeField(null=True, blank=True, verbose_name='标注时间')

    class Meta:
        db_table = 'core_sample_image'
        verbose_name = '样本图片'