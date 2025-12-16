# apps/labeler/views.py
import json
import os
import zipfile
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test

from apps.core.decorators import labeler_required
from apps.core.models import LabelTask, SampleImage, STATUS_READY
from apps.core.utils import log_operation

LABEL_CONFIG = [
    {'code': '0', 'name_cn': '0 牙齿',   'name_en': '0 Teeth',        'color': '#E74C3C'},
    {'code': '1', 'name_cn': '1 舌头',   'name_en': '1 Tongue',       'color': '#2ECC71'},
    {'code': '2', 'name_cn': '2 悬雍垂', 'name_en': '2 Uvula',        'color': '#3498DB'},
    {'code': '3', 'name_cn': '3 会厌',   'name_en': '3 Epiglottis',   'color': '#F1C40F'},
    {'code': '4', 'name_cn': '4 声门-1', 'name_en': '4 Glottis-CL-1', 'color': '#9B59B6'},
    {'code': '5', 'name_cn': '5 声门-2', 'name_en': '5 Glottis-CL-2', 'color': '#1ABC9C'},
    {'code': '6', 'name_cn': '6 声门-3', 'name_en': '6 Glottis-CL-3', 'color': '#E67E22'},
    {'code': '7', 'name_cn': '7 气管环', 'name_en': '7 Ring',         'color': '#34495E'},
    {'code': '8', 'name_cn': '8 食道',   'name_en': '8 Esophagus',    'color': '#95A5A6'},
]

@never_cache
@labeler_required
def dashboard(request):
    # 只获取状态为 "就绪" (READY) 的任务
    tasks = LabelTask.objects.filter(state=STATUS_READY).order_by('-created_at')
    
    # 初始化统计数据
    stats = {
        'total': tasks.count(),
        'not_started': 0,
        'in_progress': 0,
        'completed': 0
    }

    for task in tasks:
        # 计算进度百分比
        if task.sample_count > 0:
            task.progress = int((task.labeled_count / task.sample_count) * 100)
        else:
            task.progress = 0
            
        # ✅ [优化] 状态分类逻辑
        if task.labeled_count == 0:
            # 标注量为0 -> 未开始
            stats['not_started'] += 1
            task.status_tag = 'not_started' 
        elif task.labeled_count < task.sample_count:
            # 标注量 > 0 但 < 总量 -> 进行中
            stats['in_progress'] += 1
            task.status_tag = 'processing'
        else:
            # 标注量 >= 总量 -> 已完成
            stats['completed'] += 1
            task.status_tag = 'done'

        # 获取第一张图片ID用于跳转
        first_sample = task.samples.first()
        task.first_sample_id = first_sample.id if first_sample else None

    return render(request, 'labeler/dashboard.html', {
        'tasks': tasks,
        'stats': stats # 将统计数据传递给模板
    })

@never_cache
@labeler_required
def gallery(request, task_id):
    task = get_object_or_404(LabelTask, id=task_id)
    samples = task.samples.all()[:100]
    return render(request, 'labeler/gallery.html', {'task': task, 'samples': samples})

@never_cache
@labeler_required
def annotate_page(request, sample_id):
    sample = get_object_or_404(SampleImage, id=sample_id)
    task = sample.task
    
    next_sample = SampleImage.objects.filter(task=task, id__gt=sample.id).order_by('id').first()
    prev_sample = SampleImage.objects.filter(task=task, id__lt=sample.id).order_by('-id').first()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return JsonResponse({
            'status': 'ok',
            'sample': {
                'id': sample.id,
                'url': f"/media/{sample.file_path}",
                'name': sample.original_name,
                'annotations': json.loads(sample.annotation_content) if sample.annotation_content else []
            },
            'next_id': next_sample.id if next_sample else None,
            'prev_id': prev_sample.id if prev_sample else None
        })

    last_task_id = request.session.get('last_view_task_id')
    if last_task_id != task.id:
        log_operation(request, action="开始标注任务", target=task.name, details=f"进入任务 {task.code}")
        request.session['last_view_task_id'] = task.id

    return render(request, 'labeler/annotate.html', {
        'sample': sample,
        'next_sample': next_sample,
        'previous_sample': prev_sample,
        'task': task,
        'label_config': LABEL_CONFIG, 
    })

@require_POST
@labeler_required
def save_annotation_data(request, sample_id):
    try:
        sample = SampleImage.objects.get(id=sample_id)
        data = json.loads(request.body)
        
        sample.annotation_content = json.dumps(data.get('annotations', []), ensure_ascii=False)
        sample.is_labeled = True
        sample.labeled_by = request.user.username
        sample.labeled_at = timezone.now()
        sample.save(update_fields=['annotation_content', 'is_labeled', 'labeled_by', 'labeled_at'])
        
        task = sample.task
        task.labeled_count = task.samples.filter(is_labeled=True).count()
        task.save(update_fields=['labeled_count'])

        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'msg': str(e)}, status=500)

@never_cache
@labeler_required
def download_zip(request, task_id):
    task = get_object_or_404(LabelTask, id=task_id)
    log_operation(request, action="下载数据集", target=task.name)
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
    if request.method == 'POST':
        task = get_object_or_404(LabelTask, id=task_id)
        anno_file = request.FILES.get('annotation_file')
        if not anno_file or not anno_file.name.endswith('.zip'):
            messages.error(request, "请上传 ZIP")
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
    get_object_or_404(LabelTask, id=task_id).delete()
    return redirect('labeler:dashboard')