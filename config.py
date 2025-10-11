"""
个人网盘系统配置文件
包含系统的各种配置选项
"""

import os
from typing import List


class Settings:
    """系统设置"""
    
    # 应用基本信息
    APP_NAME: str = "个人网盘系统"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "基于FastAPI的轻量级个人云存储系统"
    
    # 服务器配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./database.db")
    
    # JWT配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    
    # 文件存储配置
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "./storage")
    TRASH_PATH: str = os.getenv("TRASH_PATH", "./trash")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(100 * 1024 * 1024)))  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [
        # 文档
        ".txt", ".md", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        # 图片
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg",
        # 音频
        ".mp3", ".wav", ".flac", ".aac", ".ogg",
        # 视频
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv",
        # 压缩文件
        ".zip", ".rar", ".7z", ".tar", ".gz",
        # 代码文件
        ".py", ".js", ".html", ".css", ".json", ".xml", ".yml", ".yaml"
    ]
    
    # 安全配置
    RATE_LIMIT_CALLS: int = int(os.getenv("RATE_LIMIT_CALLS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    TRUSTED_HOSTS: List[str] = os.getenv("TRUSTED_HOSTS", "*").split(",")
    
    # 分享配置
    DEFAULT_SHARE_EXPIRE_HOURS: int = 24 * 7  # 默认7天
    MAX_SHARE_EXPIRE_HOURS: int = 24 * 30  # 最大30天
    
    # 清理配置
    AUTO_CLEANUP_ENABLED: bool = os.getenv("AUTO_CLEANUP_ENABLED", "true").lower() == "true"
    TRASH_RETENTION_DAYS: int = int(os.getenv("TRASH_RETENTION_DAYS", "14"))
    CLEANUP_INTERVAL_HOURS: int = int(os.getenv("CLEANUP_INTERVAL_HOURS", "24"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # 预览配置
    PREVIEW_TEXT_MAX_SIZE: int = 1024 * 1024  # 1MB
    PREVIEW_IMAGE_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """验证配置的有效性"""
        errors = []
        
        # 检查必要的目录
        for path in [cls.STORAGE_PATH, cls.TRASH_PATH]:
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except Exception as e:
                    errors.append(f"无法创建目录 {path}: {e}")
        
        # 检查密钥安全性
        if cls.SECRET_KEY == "your-super-secret-key-here-change-in-production":
            errors.append("请在生产环境中更改SECRET_KEY")
        
        # 检查文件大小限制
        if cls.MAX_FILE_SIZE <= 0:
            errors.append("MAX_FILE_SIZE必须大于0")
        
        # 检查速率限制配置
        if cls.RATE_LIMIT_CALLS <= 0 or cls.RATE_LIMIT_PERIOD <= 0:
            errors.append("速率限制配置必须大于0")
        
        return errors


# 创建全局设置实例
settings = Settings()

# 生产环境安全检查
if not settings.DEBUG:
    config_errors = settings.validate_config()
    if config_errors:
        print("⚠️ 配置警告:")
        for error in config_errors:
            print(f"  - {error}")


# 环境变量配置示例
EXAMPLE_ENV = """
# 个人网盘系统环境变量配置示例
# 复制此内容到 .env 文件中并根据需要修改

# 应用配置
HOST=0.0.0.0
PORT=8000
DEBUG=false

# 数据库配置
DATABASE_URL=sqlite:///./database.db
# 如果使用MySQL: DATABASE_URL=mysql://username:password@localhost/netdisk
# 如果使用PostgreSQL: DATABASE_URL=postgresql://username:password@localhost/netdisk

# 安全配置
SECRET_KEY=your-super-secret-key-here-change-in-production-environment
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
TRUSTED_HOSTS=yourdomain.com,www.yourdomain.com

# 文件存储配置
STORAGE_PATH=./storage
TRASH_PATH=./trash
MAX_FILE_SIZE=104857600  # 100MB in bytes

# 速率限制配置
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60

# 清理配置
AUTO_CLEANUP_ENABLED=true
TRASH_RETENTION_DAYS=14
CLEANUP_INTERVAL_HOURS=24

# 日志配置
LOG_LEVEL=INFO
"""