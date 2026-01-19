# YinTu 1.0

YinTu 是一个面向医学数据的任务发布与在线标注系统，支持医院医生端（A 端）发布任务与数据处理，标注员端（B 端）进行交互式标注，并提供管理员端进行系统审计与运行监控。  
系统以数据安全、标注效率与可扩展性为核心设计目标。

---

## 一、技术栈

### 后端
- Python 3.x
- Django 5.2.7
- Django ORM
- Redis / Cache（在线用户统计）

### 前端
- AdminLTE 3
- Bootstrap 4
- HTML5 Canvas
- Vue.js 3（管理员仪表盘）
- ECharts（数据可视化）

### 其他依赖
- OpenCV（cv2）
- cryptography.fernet
- psutil
- zipfile（Python 内置）

---

## 二、系统角色说明

系统基于扩展的 `AbstractUser` 实现自定义用户模型 `UserProfile`，并区分以下三类角色：

| 角色 | 说明 |
|----|----|
| 医院医生（A 端） | 负责创建任务、上传视频及病例数据 |
| 标注员（B 端） | 负责领取任务并完成数据标注 |
| 管理员 | 负责系统管理、审计与运行监控 |

---

## 三、核心架构与权限控制

- 采用 Django 原生架构构建单体后端应用
- 通过自定义装饰器实现基于角色的访问控制（RBAC）：
  - `@hospital_required`
  - `@labeler_required`
- 权限控制逻辑集中、清晰，便于维护与扩展

---

## 四、主要功能模块

### 1. 医生端（A 端）

#### 视频处理
- 支持医学视频上传
- 使用 `threading + OpenCV` 实现后台异步抽帧
- 避免阻塞主线程，提升系统响应性能

#### 数据安全
- 使用 `cryptography.fernet` 对敏感病例文件进行对称加密存储
- 密钥统一由 `secret.key` 管理，避免明文数据落盘

#### 任务管理
- 内置任务状态机：
  - 处理中
  - 进行中
  - 已完成
  - 异常
- 前端以进度条形式展示任务处理状态

---

### 2. 标注端（B 端）

#### 在线标注工具
- 基于 HTML5 Canvas 实现多边形（Polygon）标注
- 支持精细轮廓标注，适用于医学影像数据

#### 交互特性
- 右键撤销最近点位
- Enter 键闭合多边形
- 鼠标悬停高亮标注区域

#### 多语言支持
- 支持中英文（CN / EN）标签动态切换
- 适配双语医学解剖术语场景

#### 数据流转
- 标注结果保存为 JSON 格式
- 支持数据集批量导出（Images + Labels，ZIP）
- 支持离线标注包上传并覆盖更新

---

### 3. 管理员端

#### 数据驾驶舱
- 基于 Vue.js 3 + ECharts
- 展示任务新增趋势、状态分布及标注员贡献排行

#### 系统监控
- 使用 `psutil` 实时监测：
  - CPU 使用率
  - 内存占用
  - 磁盘空间

#### 安全审计
- `OperationLog` 中间件与模型
- 记录关键操作（删除、下载、重置密码）：
  - 操作时间
  - 操作用户
  - 请求 IP

#### 中间件优化
- `DisableBrowserCacheMiddleware`：禁用敏感页面浏览器缓存
- `ActiveUserMiddleware`：统计实时在线用户数量

---

## 五、项目结构

```text
YinTu.1.0/
├── manage.py
├── secret.key
├── apps/
│   ├── core/        # 核心工具、装饰器、中间件
│   ├── users/       # 用户与管理员模块
│   ├── hospital/    # 医生端（A 端）
│   └── labeler/     # 标注端（B 端）
├── templates/
│   ├── users/
│   ├── hospital/
│   └── labeler/
└── static/
#Yintu 1.1
加入了医生端审计 头像功能
