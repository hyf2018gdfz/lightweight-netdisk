"""
文件和目录数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from app.models.user import Base
from datetime import datetime
import os


class FileNode(Base):
    """文件节点模型 - 统一管理文件和目录"""
    __tablename__ = "file_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # 文件/目录名
    path = Column(String(1000), nullable=False, index=True)  # 相对路径
    full_path = Column(String(1000), nullable=False, unique=True)  # 完整路径
    
    # 文件类型：'file' 或 'directory'
    node_type = Column(String(10), nullable=False, default='file')
    
    # 文件相关信息
    file_size = Column(BigInteger, default=0)  # 文件大小（字节）
    mime_type = Column(String(100), nullable=True)  # MIME类型
    file_extension = Column(String(10), nullable=True)  # 文件扩展名
    
    # 父目录关系
    parent_id = Column(Integer, ForeignKey('file_nodes.id'), nullable=True)
    parent = relationship("FileNode", remote_side=[id], backref="children")
    
    # 状态和时间
    is_deleted = Column(Boolean, default=False)  # 是否在回收站
    deleted_at = Column(DateTime, nullable=True)  # 删除时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 所有者
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship("User", backref="files")
    
    @property
    def is_file(self) -> bool:
        """是否为文件"""
        return self.node_type == 'file'
    
    @property
    def is_directory(self) -> bool:
        """是否为目录"""
        return self.node_type == 'directory'
    
    @property
    def physical_path(self) -> str:
        """获取物理存储路径"""
        from app.config import STORAGE_DIR, TRASH_DIR
        if self.is_deleted:
            return os.path.join(str(TRASH_DIR), self.full_path.lstrip('/'))
        return os.path.join(str(STORAGE_DIR), self.full_path.lstrip('/'))
    
    def get_children(self, include_deleted=False):
        """获取子节点"""
        query = [child for child in self.children]
        if not include_deleted:
            query = [child for child in query if not child.is_deleted]
        return query
    
    def get_all_descendants(self, include_deleted=False):
        """递归获取所有后代节点"""
        descendants = []
        for child in self.get_children(include_deleted):
            descendants.append(child)
            descendants.extend(child.get_all_descendants(include_deleted))
        return descendants
    
    def is_effectively_deleted(self):
        """检查节点是否被删除（包括通过父目录的删除状态）"""
        if self.is_deleted:
            return True
        
        # 检查父目录是否被删除
        current = self.parent
        while current:
            if current.is_deleted:
                return True
            current = current.parent
        
        return False
    
    def get_top_level_deleted_ancestor(self):
        """获取顶级被删除的祖先节点"""
        current = self
        top_deleted = None
        
        while current:
            if current.is_deleted:
                top_deleted = current
            current = current.parent
        
        return top_deleted