"""
数据库配置和初始化
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from app.config import DATABASE_URL, settings
from app.models.user import User
from app.models.file import FileNode
from app.models.share import ShareLink
import os

# 创建数据库引擎
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础模型类
Base = declarative_base()


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """获取数据库会话上下文管理器"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """初始化数据库"""
    try:
        # 确保数据库目录存在
        db_path = DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # 导入所有模型以确保表被创建
        from app.models.user import Base as UserBase
        from app.models.file import Base as FileBase
        from app.models.share import Base as ShareBase
        
        # 创建所有表
        UserBase.metadata.create_all(bind=engine)
        FileBase.metadata.create_all(bind=engine)
        ShareBase.metadata.create_all(bind=engine)
        
        # 创建默认管理员用户
        await create_default_user()
        
        print("✅ 数据库初始化完成")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise


async def create_default_user():
    """创建默认用户"""
    with get_db_context() as db:
        # 检查是否已存在用户
        admin_username = settings.DEFAULT_ADMIN_USERNAME
        existing_user = db.query(User).filter(User.username == admin_username).first()
        if existing_user:
            print("默认用户已存在")
            return
        
        # 创建默认管理员用户
        admin_password = settings.DEFAULT_ADMIN_PASSWORD
        default_user = User(
            username=admin_username,
            hashed_password=User.hash_password(admin_password),
            is_active=True
        )
        
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
        
        # 根目录不需要在数据库中创建节点，它是虚拟的
        
        if settings.DEBUG:
            print(f"✅ 默认用户创建完成 (用户名: {admin_username})")  # 不再显示密码
        else:
            print("✅ 默认管理员用户创建完成，请使用设置的凭据登录")