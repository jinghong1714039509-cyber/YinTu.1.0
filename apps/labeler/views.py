import os
import zipfile
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
# 1. 引入权限和缓存装饰器
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

# 2. 【核心修改】引入我们自定义的 B 端权限装饰器
# (确保您已经建立了 apps/core/decorators.py 文件)
from apps.core.decorators import labeler_required

from apps.core.models import LabelTask, SampleImage, STATUS_READY

# 3. 【修改】为所有视图添加 @labeler_required 装饰器
# 注意顺序：@never_cache -> @labeler_required (它里面包含了登录校验)

@never_cache
@labeler_required  # <--- ✅ 新增：只允许标注员访问，如果是医生会报错或跳走
def dashboard(request):
    """
    [B端] 首页：展示所有状态为'已就绪'的任务
    对应 urls.py 中的 path('dashboard/', ...)
    """
    # 获取所有已就绪的任务，按时间倒序排列
    tasks = LabelTask.objects.filter(state=STATUS_READY).order_by('-created_at')
    return render(request, 'labeler/dashboard.html', {'tasks': tasks})

@never_cache
@labeler_required  # <--- ✅ 新增
def gallery(request, task_id):
    """
    [B端] 图片预览墙 (分页展示防止卡顿)
    """
    task = get_object_or_404(LabelTask, id=task_id)
    # 获取前 50 张图片作为预览
    samples = task.samples.all()[:50] 
    return render(request, 'labeler/gallery.html', {'task': task, 'samples': samples})

@never_cache
@labeler_required  # <--- ✅ 新增
def download_zip(request, task_id):
    """
    [B端] 打包下载脱敏图片
    """
    task = get_object_or_404(LabelTask, id=task_id)
    
    # 对应 hospital views 中生成的图片路径: media/upload/images/{code}
    images_dir = os.path.join(settings.MEDIA_ROOT, 'upload', 'images', task.code)
    
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{task.code}_images.zip"'
    
    with zipfile.ZipFile(response, 'w') as zf:
        if os.path.exists(images_dir):
            for root, dirs, files in os.walk(images_dir):
                for file in files:
                    if file.lower().endswith(('.jpg', '.png', '.jpeg')):
                        # 在ZIP中只保留文件名，不带绝对路径
                        zf.write(os.path.join(root, file), arcname=file)
    return response

@never_cache
@labeler_required  # <--- ✅ 新增
def upload_annotation(request, task_id):
    """
    [B端] 上传标注结果 (ZIP)
    """
    if request.method == 'POST':
        task = get_object_or_404(LabelTask, id=task_id)
        anno_file = request.FILES.get('annotation_file')
        
        if not anno_file or not anno_file.name.endswith('.zip'):
            messages.error(request, "请上传 .zip 格式的压缩包")
            return redirect('labeler:gallery', task_id=task.id)

        try:
            # 解压并匹配数据库
            with zipfile.ZipFile(anno_file, 'r') as zf:
                for filename in zf.namelist():
                    # 假设标注文件名为 img_0001.xml -> 对应图片 img_0001.jpg
                    base_name = os.path.splitext(os.path.basename(filename))[0]
                    
                    # 在数据库中查找对应的样本
                    # 注意：original_name__startswith 是防止后缀不匹配
                    sample = SampleImage.objects.filter(task=task, original_name__startswith=base_name).first()
                    if sample:
                        # 读取内容并保存
                        content = zf.read(filename).decode('utf-8', errors='ignore')
                        sample.annotation_content = content
                        sample.is_labeled = True
                        # 确保 request.user 存在 (login_required 已保证)
                        sample.labeled_by = request.user.username 
                        sample.save()
            
            # 更新任务进度
            task.labeled_count = task.samples.filter(is_labeled=True).count()
            task.save()
            messages.success(request, "标注上传成功！")
            
        except Exception as e:
            messages.error(request, f"处理失败: {e}")
            
    return redirect('labeler:gallery', task_id=task.id)