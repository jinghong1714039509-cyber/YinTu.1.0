from django.db import models
from django.conf import settings

# ... (保留原有的 STATUS 常量定义) ...
STATUS_PROCESSING = 0
STATUS_READY = 1
STATUS_DONE = 2
STATUS_REVIEWING = 3
STATUS_REJECTED = 4
STATUS_ERROR = 9

class LabelTask(models.Model):
    # ... (保持原有代码不变) ...
    code = models.CharField(max_length=50, verbose_name='任务编号', unique=True)
    name = models.CharField(max_length=100, verbose_name='任务/患者名称')
    remark = models.TextField(verbose_name='病情备注', null=True, blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='创建医生')
    patient_file_path = models.CharField(max_length=500, verbose_name='加密病例路径', null=True, blank=True)
    source_video_path = models.CharField(max_length=500, verbose_name='原始视频路径', null=True, blank=True)
    video_fps = models.IntegerField(default=30, verbose_name='抽帧频率')
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

    # ✅ [新增] 审核相关字段
    AUDIT_STATUS_CHOICES = (
        (0, '待审核'),
        (1, '已通过'),
        (2, '已驳回'),
    )
    audit_status = models.IntegerField(default=0, choices=AUDIT_STATUS_CHOICES, verbose_name='审核状态')
    audit_reason = models.TextField(null=True, blank=True, verbose_name='驳回修改意见')

    class Meta:
        db_table = 'core_sample_image'
        verbose_name = '样本图片'

# ... (TaskFeedback 保持不变) ...
class TaskFeedback(models.Model):
    task = models.ForeignKey(LabelTask, on_delete=models.CASCADE, verbose_name='关联任务', null=True, blank=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_feedbacks', on_delete=models.CASCADE, verbose_name='发送人')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_feedbacks', on_delete=models.CASCADE, verbose_name='接收人', null=True, blank=True)
    content = models.TextField(verbose_name='反馈内容')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')

    class Meta:
        db_table = 'core_task_feedback'
        verbose_name = '任务反馈'
        ordering = ['-create_time']