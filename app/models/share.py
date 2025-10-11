"""
分享链接数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.user import Base
from datetime import datetime, timedelta
import secrets
import string


class ShareLink(Base):
    """分享链接模型"""
    __tablename__ = "share_links"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 分享链接标识
    share_id = Column(String(32), unique=True, index=True, nullable=False)  # 公开的分享ID
    
    # 关联的文件/目录
    file_node_id = Column(Integer, ForeignKey('file_nodes.id'), nullable=False)
    file_node = relationship("FileNode", backref="share_links")
    
    # 创建者
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    creator = relationship("User", backref="created_shares")
    
    # 分享设置
    password = Column(String(255), nullable=True)  # 访问密码（哈希）
    expire_at = Column(DateTime, nullable=True)  # 过期时间
    max_downloads = Column(Integer, nullable=True)  # 最大下载次数
    current_downloads = Column(Integer, default=0)  # 当前下载次数
    
    # 状态和时间
    is_active = Column(Boolean, default=True)  # 是否激活
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)  # 最后访问时间
    
    # 描述信息
    description = Column(Text, nullable=True)  # 分享描述
    
    @classmethod
    def generate_share_id(cls, length=8) -> str:
        """生成随机分享ID"""
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expire_at is None:
            return False
        return datetime.utcnow() > self.expire_at
    
    @property
    def is_download_limit_reached(self) -> bool:
        """检查是否达到下载限制"""
        if self.max_downloads is None:
            return False
        return self.current_downloads >= self.max_downloads
    
    @property
    def is_accessible(self) -> bool:
        """检查是否可访问"""
        return (self.is_active and 
                not self.is_expired and 
                not self.is_download_limit_reached and
                not self.file_node.is_deleted)
    
    def increment_download_count(self):
        """增加下载计数"""
        self.current_downloads += 1
        self.last_accessed = datetime.utcnow()
    
    def set_password(self, password: str):
        """设置访问密码"""
        from app.models.user import pwd_context
        self.password = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """验证访问密码"""
        if self.password is None:
            return True  # 无密码保护
        from app.models.user import pwd_context
        return pwd_context.verify(password, self.password)