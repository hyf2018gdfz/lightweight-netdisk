# 开发者指南

个人网盘系统开发环境设置和开发指南。

## 📋 开发环境要求

### 必备软件
- **Python**: 3.8+ (推荐 3.11+)
- **Git**: 版本控制
- **文本编辑器**: 推荐 VS Code、PyCharm
- **浏览器**: Chrome/Firefox（用于测试）

### 推荐工具
- **虚拟环境管理**: `venv` 或 `conda`
- **代码格式化**: `black`、`isort`
- **代码检查**: `flake8`、`pylint`
- **API 测试**: Postman、Thunder Client
- **数据库工具**: SQLite Browser、DB Browser

## 🚀 快速开始

### 1. 克隆项目

```bash
# 克隆仓库
git clone <你的仓库地址>
cd personal-netdisk

# 查看项目结构
tree -I '__pycache__|*.pyc|*.db'
```

### 2. 创建虚拟环境

```bash
# 使用 venv 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac
source venv/bin/activate

# Windows Command Prompt
venv\Scripts\activate

# Windows PowerShell
venv\Scripts\Activate.ps1
```

### 3. 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 验证安装
pip list
```

### 4. 项目初始化

```bash
# 创建必要目录（如果不存在）
mkdir -p storage trash static templates

# 设置环境变量（可选）
cp .env.example .env  # 如果有示例文件
# 或直接设置
export DEBUG=true
export SECRET_KEY=dev-secret-key
```

### 5. 启动开发服务器

```bash
# 方式一：直接运行
python main.py

# 方式二：使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 方式三：调试模式
DEBUG=true python main.py
```

访问 http://localhost:8000 开始开发！

## 🏗️ 项目架构

### 架构概览

```
个人网盘系统
├── 前端层 (Frontend)
│   ├── HTML 模板 (Jinja2)
│   ├── 静态资源 (CSS, JS)
│   └── 用户界面逻辑
├── API 层 (FastAPI)
│   ├── 路由 (Routers)
│   ├── 中间件 (Middleware)
│   └── 数据验证 (Pydantic)
├── 业务层 (Business Logic)
│   ├── 服务类 (Services)
│   ├── 工具函数 (Utils)
│   └── 数据处理逻辑
├── 数据层 (Data Layer)
│   ├── 数据模型 (SQLAlchemy)
│   ├── 数据库操作
│   └── 文件系统操作
└── 基础设施层 (Infrastructure)
    ├── 配置管理
    ├── 日志系统
    └── 安全机制
```

### 目录结构详解

```
personal-netdisk/
├── app/                          # 应用核心代码
│   ├── __init__.py              # 包初始化
│   ├── config.py                # 应用配置类
│   ├── database.py              # 数据库连接和初始化
│   │
│   ├── models/                  # 数据模型层
│   │   ├── __init__.py
│   │   ├── user.py             # 用户模型 (User)
│   │   ├── file.py             # 文件模型 (FileNode)
│   │   └── share.py            # 分享模型 (Share)
│   │
│   ├── schemas/                 # Pydantic 数据验证模式
│   │   ├── __init__.py
│   │   ├── auth.py             # 认证相关模式
│   │   ├── file.py             # 文件相关模式
│   │   └── share.py            # 分享相关模式
│   │
│   ├── routers/                 # API 路由模块
│   │   ├── __init__.py
│   │   ├── auth.py             # 认证路由 (/auth)
│   │   ├── files.py            # 文件管理路由 (/files)
│   │   ├── share.py            # 分享路由 (/share)
│   │   └── trash.py            # 回收站路由 (/trash)
│   │
│   ├── services/                # 业务逻辑服务层
│   │   ├── __init__.py
│   │   └── file_service.py     # 文件服务类
│   │
│   ├── middleware/              # 自定义中间件
│   │   ├── __init__.py
│   │   ├── security.py         # 安全头部中间件
│   │   └── rate_limit.py       # 速率限制中间件
│   │
│   └── utils/                   # 工具函数库
│       ├── __init__.py
│       ├── auth.py             # 认证工具 (JWT, 密码)
│       ├── file_utils.py       # 文件工具 (类型检测, 预览)
│       ├── file_cleaner.py     # 文件清理任务
│       └── validators.py       # 数据验证器
│
├── static/                      # 静态资源文件
│   ├── css/                    # 样式文件
│   │   ├── style.css          # 主样式文件
│   │   └── fontawesome.min.css # 图标样式
│   ├── js/                     # JavaScript 文件
│   │   └── app.js             # 主应用脚本
│   └── fonts/                  # 字体文件
│
├── templates/                   # Jinja2 HTML 模板
│   ├── index.html              # 主页面模板
│   ├── auth/                   # 认证页面模板
│   │   └── login.html         # 登录页面
│   └── share/                  # 分享页面模板
│       ├── access.html        # 分享访问页面
│       ├── password.html      # 分享密码页面
│       ├── expired.html       # 分享过期页面
│       └── not_found.html     # 分享不存在页面
│
├── storage/                     # 用户文件存储目录
├── trash/                       # 回收站目录
│
├── main.py                      # 应用入口文件
├── config.py                    # 全局配置文件
├── requirements.txt             # Python 依赖列表
├── test_system.py              # 系统测试文件
│
├── README.md                    # 项目说明
├── DEPLOYMENT.md                # 部署指南
├── DEVELOPMENT.md               # 开发指南 (本文件)
└── .gitignore                   # Git 忽略文件
```

## 🔧 开发工具配置

### VS Code 配置

创建 `.vscode/settings.json`：

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "88"],
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "*.db": true
  }
}
```

创建 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "launch",
      "program": "main.py",
      "console": "integratedTerminal",
      "env": {
        "DEBUG": "true",
        "SECRET_KEY": "dev-secret-key"
      }
    }
  ]
}
```

### PyCharm 配置

1. **解释器设置**：File → Settings → Project → Python Interpreter → 选择虚拟环境
2. **代码风格**：File → Settings → Editor → Code Style → Python → 设置为 PEP 8
3. **运行配置**：Run → Edit Configurations → 添加 Python 配置，脚本路径为 `main.py`

## 📚 核心模块详解

### 1. 数据模型 (Models)

#### User 模型 (`app/models/user.py`)
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
```

#### FileNode 模型 (`app/models/file.py`)
```python
class FileNode(Base):
    __tablename__ = "file_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    full_path = Column(String(1000), nullable=False, index=True)
    is_file = Column(Boolean, nullable=False)
    file_size = Column(BigInteger, default=0)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # ... 更多字段
```

### 2. API 路由 (Routers)

路由模块按功能分组：

- **auth.py**: 用户认证（登录、注册、验证）
- **files.py**: 文件管理（上传、下载、预览、搜索）
- **share.py**: 分享功能（创建、访问、管理分享）
- **trash.py**: 回收站（删除、恢复、清空）

### 3. 业务服务 (Services)

#### FileService (`app/services/file_service.py`)

核心业务逻辑类，负责：
- 文件节点管理
- 目录树操作
- 文件上传下载
- 权限检查

```python
class FileService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_file_node(self, ...):
        # 创建文件节点
    
    def get_node_by_path(self, ...):
        # 按路径获取节点
    
    def move_to_trash(self, ...):
        # 移动到回收站
```

### 4. 工具函数 (Utils)

- **auth.py**: JWT 令牌处理、密码加密验证
- **file_utils.py**: 文件类型检测、预览功能、图标获取
- **validators.py**: 路径验证、文件名验证
- **file_cleaner.py**: 后台清理任务

## 🔨 开发流程

### 1. 功能开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发新功能
# - 添加数据模型（如需要）
# - 创建 Pydantic 模式
# - 实现 API 路由
# - 添加业务逻辑
# - 编写前端代码

# 3. 测试功能
python test_system.py

# 4. 提交代码
git add .
git commit -m "Add new feature: description"

# 5. 合并到主分支
git checkout main
git merge feature/new-feature
```

### 2. 添加新 API 的步骤

#### 步骤 1: 定义数据模式

在 `app/schemas/` 中定义请求和响应模式：

```python
# app/schemas/example.py
from pydantic import BaseModel

class ExampleRequest(BaseModel):
    name: str
    description: str

class ExampleResponse(BaseModel):
    id: int
    name: str
    status: str
```

#### 步骤 2: 创建路由

在相应的路由文件中添加端点：

```python
# app/routers/example.py
from fastapi import APIRouter, Depends
from ..schemas.example import ExampleRequest, ExampleResponse

router = APIRouter()

@router.post("/example", response_model=ExampleResponse)
async def create_example(
    request: ExampleRequest,
    current_user: User = Depends(get_current_user)
):
    # 实现逻辑
    pass
```

#### 步骤 3: 注册路由

在 `main.py` 中注册新路由：

```python
from app.routers import example
app.include_router(example.router, prefix="/api", tags=["示例"])
```

### 3. 添加新的文件预览类型

#### 步骤 1: 扩展文件类型检测

在 `app/utils/file_utils.py` 中添加：

```python
def is_new_type(node: FileNode) -> bool:
    """检测是否为新类型文件"""
    return node.file_extension.lower() in ['.newext']

def can_preview(node: FileNode) -> bool:
    """检查文件是否可预览"""
    return (is_text_file(node) or 
            is_image(node) or 
            is_new_type(node))  # 添加新类型
```

#### 步骤 2: 实现预览逻辑

在文件路由中添加预览处理：

```python
@router.get("/preview/{node_id}")
async def preview_file(node_id: int, ...):
    # ... 现有逻辑
    elif is_new_type(node):
        # 实现新类型预览逻辑
        content = process_new_type_file(node)
        return {"type": "new_type", "content": content}
```

## 🧪 测试指南

### 运行测试

```bash
# 运行完整测试套件
python test_system.py

# 运行特定测试（如果使用 pytest）
pytest test_system.py::test_file_upload -v

# 运行测试并生成覆盖率报告
pip install coverage
coverage run test_system.py
coverage report
coverage html  # 生成 HTML 报告
```

### 手动测试

#### 1. API 测试

使用 curl 或 Postman 测试 API：

```bash
# 登录获取 token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 测试文件上传
curl -X POST "http://localhost:8000/files/upload" \
  -H "Authorization: Bearer <token>" \
  -F "files=@test.txt" \
  -F "path=/"

# 测试文件搜索
curl -X GET "http://localhost:8000/files/search?keyword=test" \
  -H "Authorization: Bearer <token>"
```

#### 2. 前端测试

1. **功能测试**：测试所有用户交互功能
2. **响应式测试**：在不同设备尺寸下测试
3. **浏览器兼容性**：测试主流浏览器
4. **性能测试**：检查页面加载速度

### 编写测试用例

```python
def test_new_feature():
    """测试新功能"""
    # 准备测试数据
    test_data = {...}
    
    # 执行测试
    response = client.post("/api/new-feature", json=test_data)
    
    # 验证结果
    assert response.status_code == 200
    assert "expected_field" in response.json()
```

## 🐛 调试技巧

### 1. 日志调试

添加日志输出：

```python
import logging

# 在函数中添加日志
logging.info(f"Processing file: {filename}")
logging.error(f"Error occurred: {str(e)}")

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)
```

### 2. 断点调试

使用 Python 调试器：

```python
import pdb; pdb.set_trace()  # 设置断点

# 或使用 VS Code 调试器
# 在代码行左侧点击设置断点，然后按 F5 启动调试
```

### 3. 数据库调试

```python
# 查看 SQL 查询
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    print("SQL:", statement)
    print("Parameters:", parameters)
```

### 4. 性能分析

```python
import time
import cProfile

# 时间测量
start_time = time.time()
# ... 代码
print(f"执行时间: {time.time() - start_time:.2f}s")

# 性能分析
cProfile.run('your_function()')
```

## 📝 代码规范

### 1. Python 代码规范

遵循 PEP 8 规范：

```python
# 好的例子
class FileService:
    """文件服务类
    
    提供文件管理相关的业务逻辑
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_file_node(
        self, 
        name: str, 
        path: str, 
        owner_id: int
    ) -> FileNode:
        """创建文件节点
        
        Args:
            name: 文件名
            path: 文件路径
            owner_id: 所有者ID
            
        Returns:
            FileNode: 创建的文件节点
        """
        # 实现逻辑
        pass
```

### 2. 前端代码规范

JavaScript 规范：

```javascript
// 好的例子
class FileManager {
    constructor(apiBase) {
        this.apiBase = apiBase;
        this.currentPath = '/';
    }
    
    async uploadFile(file, path = '/') {
        try {
            const formData = new FormData();
            formData.append('files', file);
            formData.append('path', path);
            
            const response = await this.api('/files/upload', {
                method: 'POST',
                body: formData
            });
            
            return response.json();
        } catch (error) {
            console.error('文件上传失败:', error);
            throw error;
        }
    }
}
```

### 3. 提交信息规范

Git 提交信息格式：

```bash
# 格式：type(scope): description
git commit -m "feat(files): add file search functionality"
git commit -m "fix(auth): resolve token expiration issue"
git commit -m "docs(readme): update installation guide"

# 类型说明：
# feat: 新功能
# fix: bug 修复
# docs: 文档更新
# style: 代码格式化
# refactor: 代码重构
# test: 添加或修改测试
# chore: 构建或工具相关
```

## 🔄 常见开发任务

### 1. 添加新的中间件

```python
# app/middleware/example.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class ExampleMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 请求前处理
        print(f"请求: {request.method} {request.url}")
        
        response = await call_next(request)
        
        # 响应后处理
        print(f"响应: {response.status_code}")
        return response

# main.py 中注册
app.add_middleware(ExampleMiddleware)
```

### 2. 数据库迁移

```python
# 添加新字段到模型
class FileNode(Base):
    # 现有字段...
    new_field = Column(String(100), default="")

# 创建迁移脚本（手动）
def migrate_add_new_field():
    # 连接数据库
    engine = create_engine(DATABASE_URL)
    
    # 执行 SQL
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE file_nodes ADD COLUMN new_field VARCHAR(100) DEFAULT ''"))
        conn.commit()
```

### 3. 添加新的配置项

```python
# config.py 中添加
class Settings:
    # 现有配置...
    NEW_FEATURE_ENABLED: bool = os.getenv("NEW_FEATURE_ENABLED", "false").lower() == "true"
    NEW_FEATURE_TIMEOUT: int = int(os.getenv("NEW_FEATURE_TIMEOUT", "30"))

# 使用配置
from app.config import settings

if settings.NEW_FEATURE_ENABLED:
    # 执行新功能逻辑
    pass
```

## 🚀 部署前检查

### 开发环境检查清单

- [ ] 所有测试通过
- [ ] 代码符合规范
- [ ] 没有调试代码残留
- [ ] 配置文件更新
- [ ] 文档更新完整
- [ ] 性能测试通过

### 生产环境准备

```bash
# 1. 创建生产环境配置
cat > .env.production << 'EOF'
DEBUG=false
SECRET_KEY=your-super-secure-production-key
CORS_ORIGINS=https://yourdomain.com
TRUSTED_HOSTS=yourdomain.com
DATABASE_URL=postgresql://user:pass@host/db
EOF

# 2. 安装生产依赖
pip install gunicorn

# 3. 测试生产配置
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📞 获取帮助

### 文档资源
- **FastAPI 官方文档**: https://fastapi.tiangolo.com/
- **SQLAlchemy 文档**: https://docs.sqlalchemy.org/
- **Pydantic 文档**: https://pydantic-docs.helpmanual.io/

### 常见问题
1. **导入错误**: 检查虚拟环境是否激活
2. **数据库错误**: 检查数据库文件权限
3. **端口占用**: 使用 `lsof -i :8000` 检查端口占用
4. **权限错误**: 检查文件和目录权限

### 贡献代码
欢迎提交 Issue 和 Pull Request！
1. Fork 项目
2. 创建功能分支
3. 编写测试
4. 提交 PR

---

**开发愉快！** 🎉

有问题随时查看文档或提交 Issue。