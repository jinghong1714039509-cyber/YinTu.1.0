{% extends "base_site.html" %}
{% load static %}

{% block title %}新建病例任务{% endblock %}

{% block css %}
<style>
    /* 自定义大号上传框样式 - 保持原生风格但增加可视面积 */
    .file-upload-box {
        position: relative;
        background-color: #fafafa;
        border: 2px dashed #dcdcdc; /* 浅灰色虚线，不突兀 */
        border-radius: 4px;
        height: 180px; /* 增加高度 */
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
        cursor: pointer;
        width: 100%;
        margin-bottom: 10px;
    }

    .file-upload-box:hover {
        background-color: #f2fcf5; /* 悬停微绿 */
        border-color: #1ABB9C;
    }

    .file-upload-box.has-file {
        background-color: #fff;
        border-style: solid;
        border-color: #1ABB9C;
    }

    .box-icon {
        font-size: 42px;
        color: #73879C;
        margin-bottom: 10px;
    }

    .box-text {
        font-size: 16px;
        font-weight: 600;
        color: #555;
    }

    .box-sub {
        font-size: 13px;
        color: #999;
        margin-top: 5px;
    }

    /* 文件名显示 */
    .file-name-display {
        display: none;
        margin-top: 8px;
        color: #1ABB9C;
        font-weight: bold;
        background: rgba(26, 187, 156, 0.1);
        padding: 4px 10px;
        border-radius: 20px;
    }

    /* 覆盖原生 Input 让其充满整个盒子 */
    .file-upload-box input[type="file"] {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        opacity: 0;
        cursor: pointer;
    }
</style>
{% endblock %}

{% block content %}
<div class="right_col" role="main">
    <div class="">
        <div class="page-title">
            <div class="title_left">
                <h3>新建病例任务</h3>
            </div>
        </div>
        
        <div class="clearfix"></div>

        <div class="row">
            <div class="col-md-12 col-sm-12 col-xs-12">
                <div class="x_panel">
                    <div class="x_title">
                        <h2>任务详情 <small>填写信息并上传数据</small></h2>
                        <ul class="nav navbar-right panel_toolbox">
                            <li><a class="collapse-link"><i class="fa fa-chevron-up"></i></a></li>
                            <li><a class="close-link"><i class="fa fa-close"></i></a></li>
                        </ul>
                        <div class="clearfix"></div>
                    </div>
                    
                    <div class="x_content">
                        <br />
                        
                        <form id="add-task-form" method="post" enctype="multipart/form-data" class="form-horizontal form-label-left">
                            {% csrf_token %}

                            <div class="row">
                                <div class="col-md-10 col-md-offset-1">
                                    
                                    <div class="form-group">
                                        <label class="control-label col-md-2 col-sm-2 col-xs-12" for="name">
                                            任务名称 <span class="required" style="color:red">*</span>
                                        </label>
                                        <div class="col-md-10 col-sm-10 col-xs-12">
                                            <input type="text" id="name" name="name" required="required" 
                                                   class="form-control col-md-7 col-xs-12" 
                                                   placeholder="例如：张三_喉镜检查_20231208">
                                        </div>
                                    </div>

                                    <div class="form-group">
                                        <label class="control-label col-md-2 col-sm-2 col-xs-12" for="remark">
                                            病情备注
                                        </label>
                                        <div class="col-md-10 col-sm-10 col-xs-12">
                                            <textarea id="remark" name="remark" class="form-control" rows="2" 
                                                      placeholder="可选：请填写患者主要症状..."></textarea>
                                        </div>
                                    </div>
                                    
                                </div>
                            </div>

                            <div class="ln_solid"></div>

                            <div class="row" style="margin-top: 10px;">
                                <div class="col-md-10 col-md-offset-1">
                                    <div class="row">
                                        
                                        <div class="col-md-6 col-sm-6 col-xs-12">
                                            <div class="file-upload-box" id="box-video">
                                                <input type="file" name="video_file" required accept=".mp4,.avi,.mov" onchange="handleFile(this, 'box-video')">
                                                <div class="box-icon"><i class="fa fa-film"></i></div>
                                                <div class="box-text">点击上传原始视频 <span style="color:red">*</span></div>
                                                <div class="box-sub">支持 MP4, AVI (系统自动抽帧)</div>
                                                <div class="file-name-display"><i class="fa fa-check"></i> <span></span></div>
                                            </div>
                                        </div>

                                        <div class="col-md-6 col-sm-6 col-xs-12">
                                            <div class="file-upload-box" id="box-patient">
                                                <input type="file" name="patient_file" accept=".pdf,.doc,.docx,.txt,.jpg" onchange="handleFile(this, 'box-patient')">
                                                <div class="box-icon"><i class="fa fa-file-text-o"></i></div>
                                                <div class="box-text">点击上传病例资料</div>
                                                <div class="box-sub">支持 PDF, Word, 图片 (加密存储)</div>
                                                <div class="file-name-display"><i class="fa fa-check"></i> <span></span></div>
                                            </div>
                                        </div>

                                    </div>
                                </div>
                            </div>

                            <div class="ln_solid"></div>

                            <div class="form-group">
                                <div class="col-md-12 text-center">
                                    <a href="{% url 'hospital:index' %}" class="btn btn-default btn-lg" style="margin-right: 20px;">取消</a>
                                    <button type="submit" class="btn btn-success btn-lg" id="submit-btn" style="min-width: 200px;">
                                        <i class="fa fa-cloud-upload"></i> 提交并开始处理
                                    </button>
                                </div>
                            </div>

                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block js %}
<script>
    // 通用文件选择处理
    function handleFile(input, boxId) {
        var $box = $('#' + boxId);
        var $display = $box.find('.file-name-display');
        
        if (input.files && input.files[0]) {
            var name = input.files[0].name;
            $box.addClass('has-file');
            $display.find('span').text(name);
            $display.fadeIn();
            
            // 选中视频后，图标变绿
            if(boxId === 'box-video') {
                $box.find('.box-icon').css('color', '#1ABB9C');
            }
        } else {
            $box.removeClass('has-file');
            $display.hide();
            $box.find('.box-icon').css('color', '#73879C');
        }
    }

    // 提交时的 Loading 状态
    $('#add-task-form').on('submit', function() {
        var $btn = $('#submit-btn');
        $btn.prop('disabled', true);
        $btn.html('<i class="fa fa-spinner fa-spin"></i> 正在上传并处理...');
    });
</script>
{% endblock %}