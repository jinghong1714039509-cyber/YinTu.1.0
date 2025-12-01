import os
import cv2
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from apps.core.models import LabelTask, SampleImage, STATUS_READY, STATUS_ERROR
from apps.core.utils import gen_random_code, encrypt_file

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

            # 获取当前用户 (如果没有登录，默认给 ID=1 的管理员)
            user = request.user if request.user.is_authenticated else None
            creator_id = user.id if user else 1

            task = LabelTask.objects.create(
                code=gen_random_code("TK"),
                name=name,
                remark=remark,
                creator_id=creator_id,
                state=0 # 处理中
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

            # 3. 执行抽帧 (同步执行)
            public_images_dir = os.path.join(settings.MEDIA_ROOT, 'upload', 'images', task.code)
            if not os.path.exists(public_images_dir):
                os.makedirs(public_images_dir)
            
            # 核心修改：传入 fps=1 (每秒1张)
            process_video(task, video_path, public_images_dir, extract_fps=1)

            messages.success(request, "任务创建成功！图片正在后台生成...")
            return redirect('hospital:index')

        except Exception as e:
            messages.error(request, f"创建失败: {str(e)}")
    
    return render(request, 'hospital/add_task.html')

def process_video(task, video_abs_path, output_dir, extract_fps=1):
    """
    视频抽帧逻辑 (优化版)
    extract_fps: 每秒提取几张 (默认1张)
    """
    try:
        cap = cv2.VideoCapture(video_abs_path)
        if not cap.isOpened():
            return

        # 获取视频原始帧率 (比如 30 或 60)
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        if video_fps <= 0: video_fps = 30
        
        # 计算间隔：比如视频30帧/秒，我们要1帧/秒，那间隔就是 30 帧取一次
        extract_interval = int(round(video_fps / extract_fps))
        
        frame_count = 0
        saved_count = 0

        while True:
            ret, frame = cap.read()
            if not ret: break

            # 关键逻辑：取余数为0时才保存
            if frame_count % extract_interval == 0:
                file_name = f"img_{saved_count:05d}.jpg"
                save_path = os.path.join(output_dir, file_name)
                
                # 稍微压缩一下图片质量 (quality=70)，减小体积
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
        print(f"任务 {task.code} 处理完成，保留了 {saved_count} 张图片")

    except Exception as e:
        print(f"视频处理异常: {e}")
        task.state = STATUS_ERROR
        task.save()

def index(request):
    """A端列表"""
    tasks = LabelTask.objects.all().order_by('-id')
    return render(request, 'hospital/task_list.html', {'tasks': tasks})