# 个人网盘系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于 FastAPI 的轻量级个人云存储系统，支持文件管理、分享、回收站等功能。

## ✨ 特性

### 🔐 用户认证
- JWT Token 认证
- 安全的密码存储
- 会话管理

### 📁 文件管理
- **文件上传**：支持多文件上传，拖拽上传
- **文件下载**：单文件下载，目录打包下载
- **文件预览**：支持文本、图片文件预览
- **目录管理**：无限层级目录结构
- **文件搜索**：按名称搜索文件和文件夹
- **文件操作**：重命名、删除、移动

### 🗑️ 回收站机制
- 删除文件自动移入回收站
- 支持文件恢复
- 14天自动清理过期文件
- 永久删除功能

### 📤 分享系统
- **灵活分享**：创建带密码保护的分享链接
- **访问控制**：设置过期时间和下载次数限制
- **匿名访问**：支持未登录用户访问分享内容
- **分享管理**：查看和管理已创建的分享

### 🎨 现代化界面
- **响应式设计**：适配手机、平板、电脑
- **直观操作**：现代化的用户界面
- **实时反馈**：操作状态实时显示
- **主题优化**：清爽的视觉设计

### 🔒 安全特性
- **速率限制**：防止API滥用
- **安全头部**：XSS、CSRF、点击劫持防护
- **输入验证**：严格的数据验证
- **路径安全**：防止目录遍历攻击

## 🚀 快速开始

### 系统要求
- Python 3.8+
- 512MB+ 内存
- 任意操作系统（Linux/Windows/macOS）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd personal-netdisk
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动应用**
```bash
python main.py
```

4. **访问系统**
   - 打开浏览器访问：http://localhost:8000
   - 默认账户：`admin` / `admin123`

## 📸 界面截图

### 登录界面
![登录界面](docs/images/login.png)

### 文件管理
![文件管理](docs/images/files.png)

### 分享功能
![分享功能](docs/images/share.png)

## 🛠️ 技术栈

### 后端
- **FastAPI**：现代、快速的 Web 框架
- **SQLAlchemy**：Python SQL 工具包和对象关系映射
- **Pydantic**：数据验证和设置管理
- **Python-Jose**：JWT 令牌处理
- **Passlib**：密码哈希处理

### 前端
- **HTML5/CSS3**：现代web标准
- **JavaScript (ES6+)**：交互逻辑
- **Font Awesome**：图标库
- **响应式设计**：移动设备友好

### 存储
- **SQLite**：默认数据库（可更换为 MySQL/PostgreSQL）
- **本地文件系统**：文件存储

## 📋 功能详情

### 文件操作
| 功能 | 描述 | 状态 |
|------|------|------|
| 文件上传 | 支持拖拽、多选上传 | ✅ |
| 文件下载 | 单文件/批量下载 | ✅ |
| 文件预览 | 文本、图片预览 | ✅ |
| 文件搜索 | 按名称搜索 | ✅ |
| 目录管理 | 创建、删除、浏览 | ✅ |
| 文件重命名 | 重命名文件/文件夹 | ✅ |

### 分享功能
| 功能 | 描述 | 状态 |
|------|------|------|
| 创建分享 | 生成分享链接 | ✅ |
| 密码保护 | 设置访问密码 | ✅ |
| 过期时间 | 设置链接有效期 | ✅ |
| 下载限制 | 限制下载次数 | ✅ |
| 匿名访问 | 无需登录访问 | ✅ |

### 安全功能
| 功能 | 描述 | 状态 |
|------|------|------|
| JWT 认证 | 安全的用户认证 | ✅ |
| 速率限制 | API 调用频率限制 | ✅ |
| 安全头部 | XSS、CSRF 防护 | ✅ |
| 输入验证 | 严格的数据验证 | ✅ |
| CORS 配置 | 跨域请求控制 | ✅ |

## ⚙️ 配置选项

### 环境变量

```bash
# 应用配置
HOST=0.0.0.0
PORT=8000
DEBUG=false

# 安全配置
SECRET_KEY=your-secret-key
CORS_ORIGINS=*
TRUSTED_HOSTS=*

# 文件配置
MAX_FILE_SIZE=104857600  # 100MB
STORAGE_PATH=./storage
TRASH_PATH=./trash

# 速率限制
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60
```

### 数据库配置
```bash
# SQLite (默认)
DATABASE_URL=sqlite:///./database.db

# MySQL
DATABASE_URL=mysql://user:password@localhost/netdisk

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost/netdisk
```

## 🧪 测试

运行测试套件：
```bash
python test_system.py
```

测试覆盖功能：
- ✅ 用户认证
- ✅ 文件管理
- ✅ 分享功能
- ✅ 回收站
- ✅ 安全特性
- ✅ API 接口

## 📦 部署

### Docker 部署
```bash
docker-compose up -d
```

### 传统部署

详细部署指南请参考：[DEPLOYMENT.md](DEPLOYMENT.md)

支持部署方式：
- **Docker + Docker Compose**
- **Gunicorn + Nginx**
- **Systemd 服务**
- **云平台部署**

## 🔧 开发

### 项目结构
```
personal-netdisk/
├── app/                    # 应用核心代码
│   ├── models/            # 数据模型
│   ├── routers/           # API 路由
│   ├── services/          # 业务逻辑
│   ├── utils/             # 工具函数
│   └── middleware/        # 中间件
├── static/                # 静态资源
│   ├── css/              # 样式文件
│   └── js/               # JavaScript 文件
├── templates/             # HTML 模板
├── storage/               # 文件存储目录
├── trash/                 # 回收站目录
├── main.py               # 应用入口
├── config.py             # 配置文件
└── requirements.txt      # 依赖列表
```

### 开发环境搭建

1. **克隆代码**
```bash
git clone <repository-url>
cd personal-netdisk
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\\Scripts\\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **启动开发服务器**
```bash
python main.py
```

### API 文档

启动应用后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的 Web 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL 工具包
- [Font Awesome](https://fontawesome.com/) - 图标库

## 📞 支持

如果你觉得这个项目对你有帮助，请给个 ⭐️ Star！

- 🐛 报告 Bug：[Issues](https://github.com/your-repo/issues)
- 💡 功能建议：[Discussions](https://github.com/your-repo/discussions)
- 📧 邮件支持：your-email@example.com

---

**个人网盘系统** - 让文件管理更简单 🚀