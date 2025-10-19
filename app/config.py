"""
应用配置文件
"""

import os
from pathlib import Path

# 基础配置
BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"
TRASH_DIR = BASE_DIR / "trash"
DATABASE_URL = f"sqlite:///{BASE_DIR}/netdisk.db"

# 安全配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

# 文件配置
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {
    'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'},
    'document': {'.txt', '.md', '.pdf', '.doc', '.docx'},
    'archive': {'.zip', '.rar', '.7z', '.tar', '.gz'},
    'video': {'.mp4', '.avi', '.mkv', '.mov', '.wmv'},
    'audio': {'.mp3', '.wav', '.flac', '.aac'},
}

# 预览配置
PREVIEW_EXTENSIONS = {
    'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'},
    'text': {'.txt', '.md', '.json', '.xml', '.html', '.css', '.js', '.py'},
    'pdf': {'.pdf'},
    'audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'},
    'video': {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.webm', '.m4v'}
}

# 回收站配置
TRASH_RETENTION_DAYS = 14

# 分享配置
SHARE_LINK_LENGTH = 8
MAX_SHARE_DOWNLOADS = 1000

# 管理员账户配置
DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

class Settings:
    """应用设置类"""
    DEFAULT_ADMIN_USERNAME: str = DEFAULT_ADMIN_USERNAME
    DEFAULT_ADMIN_PASSWORD: str = DEFAULT_ADMIN_PASSWORD
    SECRET_KEY: str = SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES: int = ACCESS_TOKEN_EXPIRE_MINUTES

settings = Settings()