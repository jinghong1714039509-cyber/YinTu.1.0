# apps.hospital.views
import os
import cv2
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from apps.core.models import LabelTask, SampleImage, STATUS_READY, STATUS_DONE
from apps.core.utils import gen_random_code, encrypt_file, get_cipher_suite

def add_task(request):
    """
    [A端] 新建病例任务
    对应旧代码: LabelTaskView.add
    """
    if request.method == 'POST':
        try:
            # 1. 获取参数
            name = request.POST.get('name')
            remark = request.POST.get('remark')
            video_file = request.FILES.get('video_file')
            patient_file = request.FILES.get('patient_file')

            if not name or not video_file:
                raise Exception("必须填写任务名称并上传视频")

            # 2. 创建数据库记录
            # 注意：这里简化了用户关联，默认关联到当前登录用户，如果没登录可能报错，暂用 id=1 测试
            user = request.user if request.user.is_authenticated else None
            if not user:
                # 开发测试阶段，如果未登录，先抛出错误或临时处理
                # return HttpResponse("请先创建超级管理员并登录！", status=403)
                pass 

            task = LabelTask.objects.create(
                code=gen_random_code("TK"),
                name=name,
                remark=remark,
                creator_id=user.id if user else 1, # 临时 fallback
                state=0 # 处理中
            )

            # 3. 准备目录
            # 视频和病例放在 media/secure_data/{code}/ (B端无法直接访问)
            secure_dir = os.path.join(settings.MEDIA_ROOT, 'secure_data', task.code)
            if not os.path.exists(secure_dir):
                os.makedirs(secure_dir)

            # 4. 处理加密病例
            if patient_file:
                enc_data = encrypt_file(patient_file.read())
                enc_path = os.path.join(secure_dir, 'patient.enc')
                with open(enc_path, 'wb') as f:
                    f.write(enc_data)
                task.patient_file_path = os.path.join('secure_data', task.code, 'patient.enc')

            # 5. 保存原始视频
            video_ext = os.path.splitext(video_file.name)[1]
            video_path = os.path.join(secure_dir, f'source{video_ext}')
            with open(video_path, 'wb+') as f:
                for chunk in video_file.chunks():
                    f.write(chunk)
            task.source_video_path = os.path.join('secure_data', task.code, f'source{video_ext}')
            task.save()

            # 6. 执行抽帧 (同步执行)
            # 图片放在 media/upload/images/{code}/ (B端可访问)
            public_images_dir = os.path.join(settings.MEDIA_ROOT, 'upload', 'images', task.code)
            if not os.path.exists(public_images_dir):
                os.makedirs(public_images_dir)
            
            process_video(task, video_path, public_images_dir)

            messages.success(request, "任务创建成功！")
            return redirect('hospital:index')

        except Exception as e:
            messages.error(request, f"创建失败: {str(e)}")
    
    return render(request, 'hospital/add_task.html')

def process_video(task, video_abs_path, output_dir):
    """
    视频抽帧逻辑
    """
    try:
        cap = cv2.VideoCapture(video_abs_path)
        if not cap.isOpened():
            print("无法打开视频")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0: fps = 30
        
        # 目标：每秒 30 帧，或者根据设置
        extract_interval = max(1, int(round(fps / task.video_fps)))
        
        frame_count = 0
        saved_count = 0

        while True:
            ret, frame = cap.read()
            if not ret: break

            if frame_count % extract_interval == 0:
                file_name = f"img_{saved_count:05d}.jpg"
                save_path = os.path.join(output_dir, file_name)
                cv2.imwrite(save_path, frame)

                # 写入样本表
                SampleImage.objects.create(
                    task=task,
                    code=gen_random_code("SP", 4),
                    file_path=f"upload/images/{task.code}/{file_name}",
                    original_name=file_name
                )
                saved_count += 1
            frame_count += 1
        
        cap.release()
        
        # 更新状态
        task.sample_count = saved_count
        task.state = STATUS_READY
        task.save()
        print(f"任务 {task.code} 处理完成，生成 {saved_count} 张图片")

    except Exception as e:
        print(f"视频处理异常: {e}")
        task.state = STATUS_ERROR
        task.save()

def index(request):
    """
    [A端] 任务列表页
    对应旧代码: LabelTaskView.index
    """
    tasks = LabelTask.objects.all().order_by('-id')
    return render(request, 'hospital/task_list.html', {'tasks': tasks})