# 个人网盘系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于 FastAPI 的现代化轻量级个人云存储系统，支持文件管理、分享、回收站、搜索等全面功能。

## ✨ 核心特性

### 🔐 安全认证
- **JWT Token 认证**：安全的无状态认证机制
- **密码加密存储**：使用 bcrypt 算法加密用户密码
- **访问控制**：完整的用户权限管理体系
- **速率限制**：防止 API 滥用和暴力攻击

### 📁 文件管理
- **文件上传**：支持多文件上传、拖拽上传、文件夹上传
- **文件下载**：单文件下载、文件夹打包下载（ZIP格式）
- **文件预览**：支持文本、图片、PDF、音频、视频文件预览
- **目录操作**：无限层级目录结构，支持创建、删除、重命名
- **智能搜索**：按文件名搜索，支持同名文件路径区分显示
- **文件操作**：重命名、删除、移动等完整文件操作

### 🗑️ 回收站机制
- **软删除**：删除文件自动移入回收站，避免误删
- **文件恢复**：支持从回收站恢复文件到原位置
- **自动清理**：可配置自动清理过期文件（默认14天）
- **永久删除**：支持从回收站永久删除文件

### 📤 分享系统
- **灵活分享**：创建分享链接，支持文件和文件夹分享
- **密码保护**：可选的分享密码保护功能
- **访问控制**：设置分享过期时间和下载次数限制
- **匿名访问**：支持未登录用户访问分享内容
- **分享管理**：查看、编辑和删除已创建的分享

### 🎨 现代化界面
- **响应式设计**：完美适配手机、平板、电脑等设备
- **直观操作**：现代化的用户界面，操作简单直观
- **实时反馈**：文件操作状态实时显示，进度条显示
- **主题优化**：清爽的视觉设计，使用 Font Awesome 图标

### 🔒 安全特性
- **JWT 认证**：安全的无状态认证机制，支持 Bearer Token
- **密码安全**：bcrypt 加密存储，可配置的管理员账户
- **安全头部**：XSS、CSRF、点击劫持等攻击防护
- **输入验证**：严格的数据验证和路径安全检查
- **CORS 配置**：可配置的跨域请求控制
- **可信主机**：可配置的可信主机列表
- **文件类型检测**：使用 python-magic 进行文件类型检测
- **环境变量配置**：敏感信息通过环境变量管理

## 🚀 快速开始

### 系统要求
- **Python**: 3.8+ (推荐 3.11+)
- **内存**: 512MB+ (推荐 1GB+)
- **磁盘**: 根据存储需求，建议至少 5GB 可用空间
- **操作系统**: Linux/Windows/macOS

### 三步启动

1. **克隆并安装**
```bash
git clone <你的仓库地址>
cd personal-netdisk
pip install -r requirements.txt
```

2. **启动应用**
```bash
python main.py
```

3. **开始使用**
   - 访问：http://localhost:8000
   - 首次使用：运行 `python setup_admin.py` 设置管理员密码
   - 或通过环境变量配置：`DEFAULT_ADMIN_USERNAME` 和 `DEFAULT_ADMIN_PASSWORD`

## 🛠️ 技术栈

### 后端框架
- **FastAPI 0.104.1**：现代、高性能的 Web 框架
- **Uvicorn 0.24.0**：ASGI 服务器，支持异步处理
- **SQLAlchemy 2.0.23**：强大的 Python ORM 框架
- **Pydantic**：数据验证和序列化

### 认证与安全
- **Python-Jose 3.3.0**：JWT 令牌处理
- **Passlib 1.7.4**：密码哈希和验证
- **自定义中间件**：安全头部和速率限制

### 文件处理
- **Python-Multipart 0.0.6**：文件上传处理
- **Aiofiles 23.2.1**：异步文件操作
- **Pillow 10.1.0**：图片处理和预览
- **Python-Magic 0.4.27**：文件类型识别
- **Pathvalidate 3.2.0**：路径验证和安全检查

### 前端技术
- **HTML5/CSS3**：现代 Web 标准
- **原生 JavaScript (ES6+)**：无框架依赖，轻量级
- **Font Awesome 6.0**：图标库
- **Jinja2 3.1.2**：服务端模板渲染
- **响应式设计**：移动设备优先

### 数据存储
- **SQLite**：默认数据库，零配置
- **本地文件系统**：文件存储，支持多种存储后端
- **支持扩展**：可轻松切换到 MySQL/PostgreSQL

## 📋 功能清单

### 文件操作功能
| 功能 | 描述 | 实现状态 |
|------|------|----------|
| 文件上传 | 支持拖拽、多选、文件夹上传 | ✅ 完成 |
| 文件下载 | 单文件/文件夹批量下载 | ✅ 完成 |
| 文件预览 | 文本、图片、PDF、音视频预览 | ✅ 完成 |
| 文件搜索 | 按名称搜索，路径区分显示 | ✅ 完成 |
| 目录管理 | 创建、删除、重命名目录 | ✅ 完成 |
| 文件重命名 | 重命名文件和文件夹 | ✅ 完成 |
| 路径导航 | 面包屑导航，快速跳转 | ✅ 完成 |
| 文件排序 | 按名称、时间、大小排序 | ✅ 完成 |

### 分享功能
| 功能 | 描述 | 实现状态 |
|------|------|----------|
| 创建分享 | 生成分享链接 | ✅ 完成 |
| 密码保护 | 设置分享访问密码 | ✅ 完成 |
| 过期控制 | 设置分享链接有效期 | ✅ 完成 |
| 下载限制 | 限制分享下载次数 | ✅ 完成 |
| 匿名访问 | 支持未登录用户访问分享 | ✅ 完成 |
| 分享管理 | 查看、编辑、删除分享 | ✅ 完成 |

### 安全功能
| 功能 | 描述 | 实现状态 |
|------|------|----------|
| JWT 认证 | 安全的用户认证机制 | ✅ 完成 |
| 密码加密 | bcrypt 算法加密存储 | ✅ 完成 |
| 速率限制 | API 调用频率限制 | ✅ 完成 |
| 安全头部 | XSS、CSRF、点击劫持防护 | ✅ 完成 |
| 输入验证 | 严格的数据验证和路径检查 | ✅ 完成 |
| CORS 配置 | 可配置的跨域请求控制 | ✅ 完成 |

## ⚙️ 配置选项

### 环境变量配置

所有配置都可以通过环境变量进行设置，未设置时使用默认值：

```bash
# 应用基础配置
HOST=0.0.0.0                    # 服务监听地址
PORT=8000                       # 服务端口
DEBUG=false                     # 调试模式

# 数据库配置
DATABASE_URL=sqlite:///./database.db  # 数据库连接字符串

# 安全配置
SECRET_KEY=your-secret-key      # JWT 签名密钥（生产环境必须修改）
CORS_ORIGINS=*                  # 允许的跨域源
TRUSTED_HOSTS=*                 # 可信主机列表

# 文件存储配置
STORAGE_PATH=./storage          # 文件存储路径
TRASH_PATH=./trash             # 回收站路径
MAX_FILE_SIZE=104857600        # 最大文件大小（字节，默认100MB）

# 速率限制配置
RATE_LIMIT_CALLS=100           # 限制调用次数
RATE_LIMIT_PERIOD=60           # 时间窗口（秒）

# 清理配置
AUTO_CLEANUP_ENABLED=true      # 启用自动清理
TRASH_RETENTION_DAYS=14        # 回收站保留天数
CLEANUP_INTERVAL_HOURS=24      # 清理检查间隔（小时）

# 日志配置
LOG_LEVEL=INFO                 # 日志级别

# 默认管理员配置（仅首次初始化时使用）
DEFAULT_ADMIN_USERNAME=admin   # 管理员用户名
DEFAULT_ADMIN_PASSWORD=your-secure-password  # 管理员密码
```

### 数据库配置示例

```bash
# SQLite（默认）
DATABASE_URL=sqlite:///./database.db

# MySQL
DATABASE_URL=mysql://username:password@localhost/netdisk

# PostgreSQL  
DATABASE_URL=postgresql://username:password@localhost/netdisk
```

## 🧪 测试

### 运行测试
```bash
python test_system.py
```

### 测试覆盖范围
- ✅ 用户认证和授权
- ✅ 文件上传和下载
- ✅ 文件预览功能
- ✅ 目录操作
- ✅ 分享功能
- ✅ 回收站机制
- ✅ 搜索功能
- ✅ API 接口完整性
- ✅ 安全特性验证

## 📦 部署指南

### 开发环境部署
```bash
# 直接运行
python main.py

# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 生产环境部署

详细的生产环境部署指南请参考：**[DEPLOYMENT.md](DEPLOYMENT.md)**

支持的部署方式：
- **Docker 容器化部署**（推荐）
- **Gunicorn + Nginx 部署**
- **Systemd 服务部署**
- **云平台部署**（AWS、Azure、阿里云等）

### Docker 快速部署

```bash
# 使用 Docker Compose（推荐）
docker-compose up -d

# 或直接使用 Docker
docker build -t personal-netdisk .
docker run -d -p 8000:8000 \
  -v $(pwd)/storage:/app/storage \
  -v $(pwd)/trash:/app/trash \
  personal-netdisk
```

## 🔧 开发指南

### 项目结构
```
personal-netdisk/
├── app/                       # 应用核心代码
│   ├── models/               # 数据模型定义
│   │   ├── user.py          # 用户模型
│   │   ├── file.py          # 文件模型
│   │   └── share.py         # 分享模型
│   ├── routers/             # API 路由
│   │   ├── auth.py          # 认证路由
│   │   ├── files.py         # 文件管理路由
│   │   ├── share.py         # 分享路由
│   │   └── trash.py         # 回收站路由
│   ├── services/            # 业务逻辑层
│   │   └── file_service.py  # 文件服务
│   ├── schemas/             # 数据验证模式
│   │   ├── auth.py          # 认证相关模式
│   │   ├── file.py          # 文件相关模式
│   │   └── share.py         # 分享相关模式
│   ├── utils/               # 工具函数
│   │   ├── auth.py          # 认证工具
│   │   ├── file_utils.py    # 文件工具
│   │   ├── file_cleaner.py  # 文件清理
│   │   └── validators.py    # 验证器
│   ├── middleware/          # 中间件
│   │   ├── security.py      # 安全中间件
│   │   └── rate_limit.py    # 速率限制中间件
│   ├── config.py            # 应用配置
│   └── database.py          # 数据库连接
├── static/                  # 静态资源
│   ├── css/                 # 样式文件
│   │   └── style.css        # 主样式文件
│   └── js/                  # JavaScript 文件
│       └── app.js           # 主应用脚本
├── templates/               # HTML 模板
│   ├── index.html           # 主页面模板
│   ├── auth/                # 认证相关模板
│   └── share/               # 分享页面模板
├── storage/                 # 用户文件存储目录
├── trash/                   # 回收站目录
├── main.py                  # 应用入口文件
├── config.py                # 全局配置文件
├── requirements.txt         # Python 依赖列表
├── test_system.py           # 系统测试文件
├── README.md                # 项目说明文档
└── DEPLOYMENT.md            # 部署指南文档
```

### 开发环境设置

1. **克隆代码**
```bash
git clone <你的仓库地址>
cd personal-netdisk
```

2. **创建虚拟环境**（推荐）
```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

3. **安装开发依赖**
```bash
pip install -r requirements.txt
```

4. **设置管理员账户**
```bash
# 首次运行设置管理员密码
python setup_admin.py
```

5. **启动开发服务器**
```bash
python main.py
```

### API 文档

启动应用后，可以访问以下地址查看自动生成的 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 扩展开发

系统设计采用模块化架构，便于扩展：

- **添加新的文件存储后端**：继承 `FileService` 类
- **集成第三方认证**：扩展 `auth.py` 路由
- **添加新的文件预览类型**：修改 `file_utils.py`
- **自定义中间件**：参考现有中间件实现

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出改进建议！

### 贡献方式
1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 开发规范
- 遵循 PEP 8 Python 代码规范
- 添加必要的注释和文档
- 编写测试用例覆盖新功能
- 确保所有测试通过

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🔗 相关链接

- **项目主页**: [GitHub Repository]
- **问题反馈**: [Issues]
- **功能请求**: [Feature Requests]
- **部署文档**: [DEPLOYMENT.md](DEPLOYMENT.md)

## 📞 技术支持

如遇到问题，请通过以下方式获取帮助：

1. **查看文档**：首先查看 README.md 和 DEPLOYMENT.md
2. **搜索问题**：在 Issues 中搜索类似问题
3. **提交 Issue**：详细描述问题和复现步骤
4. **社区讨论**：参与项目讨论

---

**注意**：本系统适用于个人或小团队使用。在生产环境部署前，请务必修改默认配置中的敏感信息（如 SECRET_KEY、默认密码等）。