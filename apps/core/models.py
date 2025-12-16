from django.db import models
from django.conf import settings

# ==========================================
# 1. 状态常量定义
# ==========================================
STATUS_PROCESSING = 0  # 视频正在解压/抽帧中
STATUS_READY = 1       # 就绪（可以开始标注）
STATUS_DONE = 2        # 标注完成（标注员已提交）
STATUS_REVIEWING = 3   # 待审核（医生正在检查）- ✅ [新增]
STATUS_REJECTED = 4    # 被驳回（需要标注员修改）- ✅ [新增]
STATUS_ERROR = 9       # 处理失败（视频格式错误等）

class LabelTask(models.Model):
    """
    [A端核心表] 任务与病例
    """
    # 基础信息
    code = models.CharField(max_length=50, verbose_name='任务编号', unique=True)
    name = models.CharField(max_length=100, verbose_name='任务')
    remark = models.TextField(verbose_name='病情备注', null=True, blank=True)
    
    # 归属 (关联到系统用户表)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='创建医生')
    
    # === A端上传的核心文件 ===
    patient_file_path = models.CharField(max_length=500, verbose_name='加密病例路径', null=True, blank=True)
    source_video_path = models.CharField(max_length=500, verbose_name='原始视频路径', null=True, blank=True)
    
    # 处理设置
    video_fps = models.IntegerField(default=30, verbose_name='抽帧频率')
    
    # 状态与统计
    sample_count = models.IntegerField(default=0, verbose_name='样本数量')
    labeled_count = models.IntegerField(default=0, verbose_name='已标注数')
    
    # state 字段使用上面的常量
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

class TaskFeedback(models.Model):
    """
    ✅ [新增] 任务反馈/私信表
    用于实现：
    1. 医生驳回任务时填写修改意见
    2. 管理员发送私信通知
    """
    # 关联任务 (如果是私信，可以为空)
    task = models.ForeignKey(LabelTask, on_delete=models.CASCADE, verbose_name='关联任务', null=True, blank=True)
    
    # 发送者与接收者
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_feedbacks', on_delete=models.CASCADE, verbose_name='发送人')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_feedbacks', on_delete=models.CASCADE, verbose_name='接收人', null=True, blank=True)
    
    # 反馈详情
    content = models.TextField(verbose_name='反馈内容')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')

    class Meta:
        db_table = 'core_task_feedback'
        verbose_name = '任务反馈'
        ordering = ['-create_time']