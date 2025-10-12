"""
轻量级个人网盘系统 - 主入口
基于FastAPI框架，支持文件管理、分享、回收站等功能
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import os

# 导入路由模块
from app.routers import auth, files, share, trash
from app.database import init_db
from app.utils.file_cleaner import start_file_cleaner
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

# 创建必要的目录
os.makedirs("storage", exist_ok=True)
os.makedirs("trash", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    await init_db()
    start_file_cleaner()  # 启动文件清理任务
    print("🚀 个人网盘系统启动成功")
    
    yield
    
    # 关闭时执行
    print("📁 个人网盘系统已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="个人网盘系统",
    description="轻量级个人网盘，支持文件管理和分享功能",
    version="1.0.0",
    lifespan=lifespan
)

# 添加安全中间件
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)  # 每分钟100次请求

# 添加可信主机中间件（生产环境中应配置具体域名）
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # 开发环境允许所有主机
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应配置具体域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="templates")

# 注册路由
app.include_router(auth.router, prefix="/auth", tags=["认证"])
app.include_router(files.router, prefix="/files", tags=["文件管理"])
app.include_router(trash.router, prefix="/trash", tags=["回收站"])
app.include_router(share.router, prefix="/share", tags=["分享系统"])


@app.get("/")
async def index(request: Request):
    """首页/根目录"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/trash")
async def trash_page(request: Request):
    """回收站页面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/{path:path}")
async def folder_path(request: Request, path: str):
    """文件夹路径页面"""
    # 避免与 API 路径冲突
    if path.startswith(("auth/", "files/", "trash/", "share/", "health", "static/")):
        raise HTTPException(status_code=404, detail="Not found")
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "个人网盘系统运行正常"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )