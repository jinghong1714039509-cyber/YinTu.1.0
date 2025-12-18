import os
import cv2
import json
import threading
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.db import connection
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# 引入装饰器
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from apps.core.decorators import hospital_required 

# 引入核心模型
from apps.core.models import LabelTask, SampleImage, STATUS_READY, STATUS_ERROR
from apps.core.utils import gen_random_code, encrypt_file, log_operation

@never_cache
@hospital_required
def add_task(request):
    """A端：新建任务"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            remark = request.POST.get('remark')
            video_file = request.FILES.get('video_file')
            patient_file = request.FILES.get('patient_file')

            if not name or not video_file:
                raise Exception("必须填写任务名称并上传视频")

            user = request.user 
            creator_id = user.id

            # 创建任务，初始状态为 0 (处理中)
            task = LabelTask.objects.create(
                code=gen_random_code("TK"),
                name=name,
                remark=remark,
                creator_id=creator_id,
                state=0 
            )

            # 1. 保存加密文件 (如果有)
            secure_dir = os.path.join(settings.MEDIA_ROOT, 'secure_data', task.code)
            if not os.path.exists(secure_dir):
                os.makedirs(secure_dir)

            if patient_file:
                enc_data = encrypt_file(patient_file.read())
                enc_path = os.path.join(secure_dir, 'patient.enc')
                with open(enc_path, 'wb') as f:
                    f.write(enc_data)
                task.patient_file_path = os.path.join('secure_data', task.code, 'patient.enc')

            # 2. 保存原始视频
            video_ext = os.path.splitext(video_file.name)[1]
            video_path = os.path.join(secure_dir, f'source{video_ext}')
            with open(video_path, 'wb+') as f:
                for chunk in video_file.chunks():
                    f.write(chunk)
            task.source_video_path = os.path.join('secure_data', task.code, f'source{video_ext}')
            task.save()

            # 3. 启动异步线程执行抽帧
            public_images_dir = os.path.join(settings.MEDIA_ROOT, 'upload', 'images', task.code)
            if not os.path.exists(public_images_dir):
                os.makedirs(public_images_dir)
            
            thread = threading.Thread(
                target=process_video_thread,
                args=(task.id, video_path, public_images_dir, 1)
            )
            thread.start()

            # 记录日志
            log_operation(
                request, 
                action="新建任务", 
                target=task.name, 
                details=f"任务 {task.code} 已创建，后台正在解压处理视频..."
            )

            messages.success(request, "任务创建成功！视频正在后台处理，请稍后刷新查看进度。")
            return redirect('hospital:index')

        except Exception as e:
            messages.error(request, f"创建失败: {str(e)}")
    
    return render(request, 'hospital/add_task.html')

def process_video_thread(task_id, video_abs_path, output_dir, extract_fps=1):
    """
    线程安全的视频处理函数
    """
    try:
        connection.close() 
        task = LabelTask.objects.get(id=task_id)
        process_video_logic(task, video_abs_path, output_dir, extract_fps)
    except Exception as e:
        print(f"线程异常: {e}")
    finally:
        connection.close()

def process_video_logic(task, video_abs_path, output_dir, extract_fps=1):
    """
    原有的处理逻辑
    """
    try:
        cap = cv2.VideoCapture(video_abs_path)
        if not cap.isOpened():
            task.state = STATUS_ERROR
            task.save()
            return

        video_fps = cap.get(cv2.CAP_PROP_FPS)
        if video_fps <= 0: video_fps = 30
        
        extract_interval = int(round(video_fps / extract_fps))
        
        frame_count = 0
        saved_count = 0

        while True:
            ret, frame = cap.read()
            if not ret: break

            if frame_count % extract_interval == 0:
                file_name = f"img_{saved_count:05d}.jpg"
                save_path = os.path.join(output_dir, file_name)
                cv2.imwrite(save_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])

                SampleImage.objects.create(
                    task=task,
                    code=gen_random_code("SP", 4),
                    file_path=f"upload/images/{task.code}/{file_name}",
                    original_name=file_name
                )
                saved_count += 1
            frame_count += 1
        
        cap.release()
        
        task.sample_count = saved_count
        task.state = STATUS_READY
        task.save()
        print(f"✅ 任务 {task.code} 后台处理完成，生成 {saved_count} 张图片")

    except Exception as e:
        print(f"❌ 视频处理异常: {e}")
        task.state = STATUS_ERROR
        task.save()

@never_cache
@hospital_required
def index(request):
    """
    A端任务列表
    """
    # 1. 获取所有任务（倒序）
    task_list = LabelTask.objects.all().order_by('-id')
    
    # 2. 计算每个任务的进度（为了在卡片上显示进度条）
    for task in task_list:
        if task.sample_count > 0:
            task.progress = int((task.labeled_count / task.sample_count) * 100)
        else:
            task.progress = 0

    # 3. 分页处理：每页 12 个任务
    paginator = Paginator(task_list, 12)
    page = request.GET.get('page')
    
    try:
        tasks = paginator.page(page)
    except PageNotAnInteger:
        tasks = paginator.page(1)
    except EmptyPage:
        tasks = paginator.page(paginator.num_pages)

    return render(request, 'hospital/task_list.html', {'tasks': tasks})

# ==========================================
#  ✅ 新增：审核功能相关视图
# ==========================================

@never_cache
@hospital_required
def audit_workspace(request, task_id):
    """
    [新增] 医生审核工作台 (与标注界面类似，但侧重于审核操作)
    """
    task = get_object_or_404(LabelTask, id=task_id)

    # === AJAX 请求处理：获取图片数据 ===
    if request.GET.get('ajax'):
        sample_id = request.GET.get('sample_id')
        
        # 查找逻辑：
        # 1. 如果指定了 sample_id，就查那张
        # 2. 如果没指定，优先查第一张【未审核】且【已标注】的图片
        # 3. 如果都审核完了，就查第一张图片
        if sample_id:
            sample = SampleImage.objects.filter(id=sample_id, task=task).first()
        else:
            sample = SampleImage.objects.filter(task=task, is_labeled=True, audit_status=0).first()
            if not sample:
                sample = SampleImage.objects.filter(task=task).first()
        
        if not sample:
            return JsonResponse({'status': 'empty', 'msg': '暂无样本'})

        # 获取上一张/下一张 ID (方便切换)
        prev_obj = SampleImage.objects.filter(task=task, id__lt=sample.id).order_by('-id').first()
        next_obj = SampleImage.objects.filter(task=task, id__gt=sample.id).order_by('id').first()

        # 解析标注数据
        annotations = []
        if sample.annotation_content:
            try:
                annotations = json.loads(sample.annotation_content)
            except:
                annotations = []

        return JsonResponse({
            'status': 'ok',
            'sample': {
                'id': sample.id,
                'url': f"/media/{sample.file_path}",
                'name': sample.original_name,
                'is_labeled': sample.is_labeled,
                'annotations': annotations,
                # 审核相关
                'audit_status': sample.audit_status,
                'audit_reason': sample.audit_reason or ''
            },
            'prev_id': prev_obj.id if prev_obj else None,
            'next_id': next_obj.id if next_obj else None
        })

    # === 普通页面加载 ===
    # 模拟一个标签配置 (实际应从数据库读取，这里暂时硬编码)
    label_config = [
        {'code': 'nodule', 'name_cn': '肺结节', 'color': '#e74c3c'},
        {'code': 'fracture', 'name_cn': '骨折', 'color': '#f1c40f'},
        {'code': 'mass', 'name_cn': '肿块', 'color': '#9b59b6'},
    ]
    return render(request, 'hospital/audit.html', {
        'task': task, 
        'label_config': label_config
    })

@csrf_exempt
@hospital_required
def save_audit_result(request):
    """
    [新增] 保存审核结果 API
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sample_id = data.get('sample_id')
            status = int(data.get('status')) # 1:通过, 2:驳回
            reason = data.get('reason', '')

            sample = get_object_or_404(SampleImage, id=sample_id)
            sample.audit_status = status
            sample.audit_reason = reason
            sample.save()
            
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'msg': str(e)})
    return JsonResponse({'status': 'error', 'msg': 'Method not allowed'})