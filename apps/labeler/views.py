# apps/labeler/views.py
import os
import zipfile
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
# 引入自定义装饰器
from apps.core.decorators import labeler_required
from apps.core.models import LabelTask, SampleImage, STATUS_READY
# 引入日志工具
from apps.core.utils import log_operation

# ==========================================
# 1. 全局配置：解剖部位标签 (双语版)
# ==========================================
LABEL_CONFIG = [
    {'code': '0', 'name_cn': '0 牙齿',   'name_en': '0 Teeth',        'color': '#E74C3C'}, # 红
    {'code': '1', 'name_cn': '1 舌头',   'name_en': '1 Tongue',       'color': '#2ECC71'}, # 绿
    {'code': '2', 'name_cn': '2 悬雍垂', 'name_en': '2 Uvula',        'color': '#3498DB'}, # 蓝
    {'code': '3', 'name_cn': '3 会厌',   'name_en': '3 Epiglottis',   'color': '#F1C40F'}, # 黄
    {'code': '4', 'name_cn': '4 声门-1', 'name_en': '4 Glottis-CL-1', 'color': '#9B59B6'}, # 紫
    {'code': '5', 'name_cn': '5 声门-2', 'name_en': '5 Glottis-CL-2', 'color': '#1ABC9C'}, # 青
    {'code': '6', 'name_cn': '6 声门-3', 'name_en': '6 Glottis-CL-3', 'color': '#E67E22'}, # 橙
    {'code': '7', 'name_cn': '7 气管环', 'name_en': '7 Ring',         'color': '#34495E'}, # 深蓝
    {'code': '8', 'name_cn': '8 食道',   'name_en': '8 Esophagus',    'color': '#95A5A6'}, # 灰
]

# ==========================================
# 2. 视图函数
# ==========================================

@never_cache
@labeler_required
def dashboard(request):
    """[B端] 首页：卡片化展示任务"""
    tasks = LabelTask.objects.filter(state=STATUS_READY).order_by('-created_at')
    
    # 预处理数据
    for task in tasks:
        if task.sample_count > 0:
            task.progress = int((task.labeled_count / task.sample_count) * 100)
        else:
            task.progress = 0
        
        # 获取第一张图片作为入口
        first_sample = task.samples.first()
        task.first_sample_id = first_sample.id if first_sample else None

    return render(request, 'labeler/dashboard.html', {'tasks': tasks})

@never_cache
@labeler_required
def gallery(request, task_id):
    """[B端] 图片预览墙"""
    task = get_object_or_404(LabelTask, id=task_id)
    samples = task.samples.all()[:100]
    return render(request, 'labeler/gallery.html', {'task': task, 'samples': samples})

@never_cache
@labeler_required
def annotate_page(request, sample_id):
    """[B端] 在线标注工作台"""
    sample = get_object_or_404(SampleImage, id=sample_id)
    task = sample.task
    
    # 获取下一张图片
    next_sample = SampleImage.objects.filter(
        task=task, 
        id__gt=sample.id
    ).order_by('id').first()

    # ✅ 【优化日志逻辑】：利用 Session 防抖动
    # 只有当 Session 里记录的 'last_view_task' 与当前不一致时，才记录日志
    # 这样用户在同一个任务里点 "下一张" 不会产生刷屏日志
    last_task_id = request.session.get('last_view_task_id')
    
    if last_task_id != task.id:
        log_operation(
            request, 
            action="开始标注任务", 
            target=task.name, 
            details=f"用户进入了任务 {task.code} 的标注工作台"
        )
        # 更新 Session 状态
        request.session['last_view_task_id'] = task.id

    return render(request, 'labeler/annotate.html', {
        'sample': sample,
        'next_sample': next_sample,
        'task': task,
        'label_config': LABEL_CONFIG, 
    })

@require_POST
@labeler_required
def save_annotation_data(request, sample_id):
    """[API] 保存标注数据"""
    sample = get_object_or_404(SampleImage, id=sample_id)
    try:
        data = json.loads(request.body)
        annotations = data.get('annotations', [])
        
        # 保存
        sample.annotation_content = json.dumps(annotations, ensure_ascii=False)
        sample.is_labeled = True
        sample.labeled_by = request.user.username
        sample.labeled_at = timezone.now()
        sample.save()
        
        # 更新任务进度
        task = sample.task
        task.labeled_count = task.samples.filter(is_labeled=True).count()
        task.save()

        # ✅ 保存是一个明确的操作动作，建议保留记录，或者改为"每10次保存记录一次"
        # 这里为了防止太频繁，可以把保存日志也注释掉，或者只记录关键信息
        # 如果您觉得保存也不需要记录，可以删掉下面这段：
        log_operation(
            request, 
            action="保存标注", 
            target=sample.original_name, 
            details=f"用户 {request.user.username} 更新了标注数据"
        )

        return JsonResponse({'status': 'ok', 'msg': '保存成功'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'msg': str(e)}, status=500)

@never_cache
@labeler_required
def download_zip(request, task_id):
    """[B端] 下载"""
    task = get_object_or_404(LabelTask, id=task_id)
    
    # 下载属于低频高危操作，建议保留日志
    log_operation(
        request, 
        action="下载数据集", 
        target=task.name, 
        details=f"下载任务 {task.code} 的所有图片"
    )

    images_dir = os.path.join(settings.MEDIA_ROOT, 'upload', 'images', task.code)
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{task.code}_images.zip"'
    
    with zipfile.ZipFile(response, 'w') as zf:
        if os.path.exists(images_dir):
            for root, dirs, files in os.walk(images_dir):
                for file in files:
                    if file.lower().endswith(('.jpg', '.png', '.jpeg')):
                        zf.write(os.path.join(root, file), arcname=file)
    return response

@never_cache
@labeler_required
def upload_annotation(request, task_id):
    """[B端] 上传"""
    if request.method == 'POST':
        task = get_object_or_404(LabelTask, id=task_id)
        anno_file = request.FILES.get('annotation_file')
        
        if not anno_file or not anno_file.name.endswith('.zip'):
            messages.error(request, "请上传 ZIP 格式")
            return redirect('labeler:gallery', task_id=task.id)

        try:
            with zipfile.ZipFile(anno_file, 'r') as zf:
                for filename in zf.namelist():
                    base_name = os.path.splitext(os.path.basename(filename))[0]
                    sample = SampleImage.objects.filter(task=task, original_name__startswith=base_name).first()
                    if sample:
                        sample.annotation_content = zf.read(filename).decode('utf-8', errors='ignore')
                        sample.is_labeled = True
                        sample.labeled_by = request.user.username 
                        sample.save()
            task.labeled_count = task.samples.filter(is_labeled=True).count()
            task.save()

            log_operation(
                request, 
                action="上传标注包", 
                target=task.name, 
                details="批量上传覆盖标注数据"
            )

            messages.success(request, "上传成功")
        except Exception as e:
            messages.error(request, f"失败: {e}")
            
    return redirect('labeler:gallery', task_id=task.id)

def is_superuser(user):
    return user.is_superuser

@never_cache
@login_required
@user_passes_test(is_superuser)  
def delete_task(request, task_id):
    """
    [管理员功能] 删除任务及关联文件
    """
    task = get_object_or_404(LabelTask, id=task_id)
    task_code = task.code 
    
    task.delete()
    
    log_operation(
        request, 
        action="删除任务", 
        target=task_code, 
        details="管理员强制删除了任务"
    )

    messages.success(request, f"任务 {task_code} 已删除")
    return redirect('labeler:dashboard')