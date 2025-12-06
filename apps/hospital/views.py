import os
import cv2
import threading
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.db import connection
# 引入装饰器
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from apps.core.decorators import hospital_required 

from apps.core.models import LabelTask, SampleImage, STATUS_READY, STATUS_ERROR
# ✅ 修改：引入 log_operation
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

            # 3. ✅ 关键修改：启动异步线程执行抽帧
            public_images_dir = os.path.join(settings.MEDIA_ROOT, 'upload', 'images', task.code)
            if not os.path.exists(public_images_dir):
                os.makedirs(public_images_dir)
            
            # 使用 Thread 开启后台任务
            thread = threading.Thread(
                target=process_video_thread,  # 指向下面的新函数
                args=(task.id, video_path, public_images_dir, 1) # 传 ID 而不是对象，防止线程冲突
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
    ✅ 新增：线程安全的视频处理函数
    """
    # 在线程开始时，重新获取 task 对象，避免数据库连接问题
    try:
        # 显式关闭旧连接，强制线程建立新连接
        connection.close() 
        task = LabelTask.objects.get(id=task_id)
        
        process_video_logic(task, video_abs_path, output_dir, extract_fps)
        
    except Exception as e:
        print(f"线程异常: {e}")
    finally:
        connection.close()

def process_video_logic(task, video_abs_path, output_dir, extract_fps=1):
    """
    原有的处理逻辑，移动到这里
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
                
                # 压缩图片质量，进一步减少卡顿和存储
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
    """A端列表"""
    # 还可以加一步：只显示当前用户创建的任务 (可选)
    # if not request.user.is_superuser:
    #     tasks = LabelTask.objects.filter(creator_id=request.user.id).order_by('-id')
    # else:
    tasks = LabelTask.objects.all().order_by('-id')
    return render(request, 'hospital/task_list.html', {'tasks': tasks})