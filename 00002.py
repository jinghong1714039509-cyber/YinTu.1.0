import os

# 1. 直接使用报错信息里的绝对路径，确保万无一失
project_root = r'C:\Users\Administrator\Desktop\YinTu.1.0'
templates_dir = os.path.join(project_root, 'templates')
target_file = os.path.join(templates_dir, 'base_site.html')

print(f"🔍 正在检查路径: {templates_dir}")

# 2. 强制创建目录（如果不存在）
if not os.path.exists(templates_dir):
    print("⚠️ templates 目录不存在，正在创建...")
    os.makedirs(templates_dir)
else:
    print(f"✅ templates 目录存在。当前内容: {os.listdir(templates_dir)}")

# 3. 强制写入 base_site.html 内容
html_content = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}医疗数据平台{% endblock %}</title>
    
    <link href="/static/vendors/bootstrap/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="/static/vendors/font-awesome/css/font-awesome.min.css" rel="stylesheet">
    <link href="/static/vendors/nprogress/nprogress.css" rel="stylesheet">
    <link href="/static/build/css/custom.min.css" rel="stylesheet">
    
    <style>
        .nav-md .container.body .col-md-3.left_col { min-height: 100%; }
        .right_col { min-height: 100vh !important; }
    </style>
    {% block css %}{% endblock %}
</head>

<body class="nav-md">
    <div class="container body">
        <div class="main_container">
            <div class="col-md-3 left_col">
                <div class="left_col scroll-view">
                    <div class="navbar nav_title" style="border: 0;">
                        <a href="/" class="site_title"><i class="fa fa-heartbeat"></i> <span>YinTu 医疗</span></a>
                    </div>
                    <div class="clearfix"></div>
                    <br />
                    <div id="sidebar-menu" class="main_menu_side hidden-print main_menu">
                        <div class="menu_section">
                            <h3>A端 / 医院</h3>
                            <ul class="nav side-menu">
                                <li><a href="/hospital/add/"><i class="fa fa-plus"></i> 新建病例任务</a></li>
                                <li><a href="/hospital/list/"><i class="fa fa-list"></i> 任务列表</a></li>
                            </ul>
                        </div>
                        <div class="menu_section">
                            <h3>B端 / 标注</h3>
                            <ul class="nav side-menu">
                                <li><a href="/labeler/dashboard/"><i class="fa fa-folder-open"></i> 标注工作台</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <div class="top_nav">
                <div class="nav_menu">
                    <nav>
                        <div class="nav toggle"><a id="menu_toggle"><i class="fa fa-bars"></i></a></div>
                        <ul class="nav navbar-nav navbar-right">
                            <li><a href="javascript:;" class="user-profile">管理员</a></li>
                        </ul>
                    </nav>
                </div>
            </div>

            {% block content %}{% endblock %}
            
            <footer><div class="pull-right">YinTu System</div><div class="clearfix"></div></footer>
        </div>
    </div>

    <script src="/static/vendors/jquery/dist/jquery.min.js"></script>
    <script src="/static/vendors/bootstrap/dist/js/bootstrap.min.js"></script>
    <script src="/static/vendors/fastclick/lib/fastclick.js"></script>
    <script src="/static/vendors/nprogress/nprogress.js"></script>
    <script src="/static/build/js/custom.min.js"></script>
    {% block js %}{% endblock %}
</body>
</html>
"""

try:
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("-" * 30)
    print(f"🚀 成功！文件已强制写入: {target_file}")
    print(f"再次检查文件是否存在: {os.path.exists(target_file)}")
    print("-" * 30)
except Exception as e:
    print(f"❌ 写入失败: {e}")