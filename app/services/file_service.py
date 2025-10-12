"""
文件管理服务
"""

import os
import shutil
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.file import FileNode
from app.models.user import User
from app.config import STORAGE_DIR, TRASH_DIR
import mimetypes
import magic


class FileService:
    """文件管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def get_node_by_path(self, path: str, user: User, include_deleted: bool = False) -> Optional[FileNode]:
        """根据路径获取文件节点"""
        query = self.db.query(FileNode).filter(
            FileNode.full_path == path,
            FileNode.owner_id == user.id
        )
        
        if not include_deleted:
            query = query.filter(FileNode.is_deleted == False)
            
        return query.first()
    
    def get_node_by_id(self, node_id: int, user: User, include_deleted: bool = False) -> Optional[FileNode]:
        """根据ID获取文件节点"""
        query = self.db.query(FileNode).filter(
            FileNode.id == node_id,
            FileNode.owner_id == user.id
        )
        
        if not include_deleted:
            query = query.filter(FileNode.is_deleted == False)
            
        return query.first()
    
    def get_children(self, parent_path: str, user: User, include_deleted: bool = False) -> List[FileNode]:
        """获取目录下的子节点"""
        # 特殊处理根目录
        if parent_path == "/":
            # 根目录：查询所有parent_id为None的节点
            query = self.db.query(FileNode).filter(
                FileNode.parent_id.is_(None),
                FileNode.owner_id == user.id
            )
            if not include_deleted:
                query = query.filter(FileNode.is_deleted == False)
            return query.order_by(FileNode.node_type.desc(), FileNode.name).all()
        
        # 非根目录：按原有逻辑处理
        parent_node = self.get_node_by_path(parent_path, user, include_deleted)
        if not parent_node or not parent_node.is_directory:
            return []
        
        query = self.db.query(FileNode).filter(
            FileNode.parent_id == parent_node.id,
            FileNode.owner_id == user.id
        )
        
        if not include_deleted:
            query = query.filter(FileNode.is_deleted == False)
            
        return query.order_by(FileNode.node_type.desc(), FileNode.name).all()
    
    def create_directory(self, path: str, user: User) -> FileNode:
        """创建目录"""
        # 检查路径是否已存在
        if self.get_node_by_path(path, user):
            raise ValueError(f"路径 {path} 已存在")
        
        # 解析路径
        parent_path = os.path.dirname(path)
        dir_name = os.path.basename(path)
        
        # 获取父目录
        parent_id = None
        if parent_path != "/":
            parent_node = self.get_node_by_path(parent_path, user)
            if not parent_node:
                # 递归创建父目录
                parent_node = self.create_directory(parent_path, user)
            parent_id = parent_node.id
        
        # 创建物理目录
        physical_path = os.path.join(STORAGE_DIR, path.lstrip('/'))
        os.makedirs(physical_path, exist_ok=True)
        
        # 创建数据库记录
        dir_node = FileNode(
            name=dir_name,
            path=path,
            full_path=path,
            node_type='directory',
            parent_id=parent_id,
            owner_id=user.id
        )
        
        self.db.add(dir_node)
        self.db.commit()
        self.db.refresh(dir_node)
        
        return dir_node
    
    def ensure_directory_exists(self, path: str, user: User) -> FileNode:
        """确保目录存在，不存在则创建"""
        # 根目录特殊处理：始终返回None（因为根目录没有parent_id）
        if path == "/":
            return None
        
        node = self.get_node_by_path(path, user)
        if node:
            if not node.is_directory:
                raise ValueError(f"路径 {path} 不是目录")
            return node
        return self.create_directory(path, user)
    
    def save_uploaded_file(self, file_path: str, content: bytes, user: User) -> FileNode:
        """保存上传的文件"""
        # 检查路径是否已存在
        if self.get_node_by_path(file_path, user):
            raise ValueError(f"文件 {file_path} 已存在")
        
        # 解析路径
        parent_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        
        # 确保父目录存在
        parent_node = self.ensure_directory_exists(parent_path, user)
        parent_id = parent_node.id if parent_node else None
        
        # 创建物理文件
        physical_path = os.path.join(STORAGE_DIR, file_path.lstrip('/'))
        os.makedirs(os.path.dirname(physical_path), exist_ok=True)
        
        with open(physical_path, 'wb') as f:
            f.write(content)
        
        # 获取文件信息
        file_size = len(content)
        file_extension = os.path.splitext(file_name)[1].lower()
        
        # 检测MIME类型
        mime_type = None
        try:
            mime_type = magic.from_buffer(content, mime=True)
        except:
            # 如果magic失败，使用mimetypes模块
            mime_type, _ = mimetypes.guess_type(file_name)
        
        # 创建数据库记录
        file_node = FileNode(
            name=file_name,
            path=file_path,
            full_path=file_path,
            node_type='file',
            file_size=file_size,
            mime_type=mime_type,
            file_extension=file_extension,
            parent_id=parent_id,
            owner_id=user.id
        )
        
        self.db.add(file_node)
        self.db.commit()
        self.db.refresh(file_node)
        
        return file_node
    
    def move_to_trash(self, node: FileNode) -> bool:
        """移动文件/目录到回收站"""
        if node.is_deleted:
            return False
        
        # 移动物理文件
        old_path = node.physical_path
        if os.path.exists(old_path):
            trash_path = os.path.join(TRASH_DIR, node.full_path.lstrip('/'))
            os.makedirs(os.path.dirname(trash_path), exist_ok=True)
            shutil.move(old_path, trash_path)
        
        # 更新数据库记录
        node.is_deleted = True
        node.deleted_at = datetime.utcnow()
        
        # 如果是目录，递归删除子节点
        if node.is_directory:
            for child in node.get_all_descendants():
                child.is_deleted = True
                child.deleted_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def restore_from_trash(self, node: FileNode) -> bool:
        """从回收站恢复文件/目录"""
        if not node.is_deleted:
            return False
        
        # 检查目标路径是否已存在
        if self.get_node_by_path(node.full_path, node.owner):
            raise ValueError(f"恢复失败：路径 {node.full_path} 已存在")
        
        # 移动物理文件
        trash_path = os.path.join(TRASH_DIR, node.full_path.lstrip('/'))
        if os.path.exists(trash_path):
            restore_path = os.path.join(STORAGE_DIR, node.full_path.lstrip('/'))
            os.makedirs(os.path.dirname(restore_path), exist_ok=True)
            shutil.move(trash_path, restore_path)
        
        # 更新数据库记录
        node.is_deleted = False
        node.deleted_at = None
        
        # 如果是目录，递归恢复子节点
        if node.is_directory:
            for child in node.get_all_descendants(include_deleted=True):
                if child.is_deleted:
                    child.is_deleted = False
                    child.deleted_at = None
        
        self.db.commit()
        return True
    
    def permanent_delete(self, node: FileNode) -> bool:
        """永久删除文件/目录"""
        if not node.is_deleted:
            return False
        
        # 删除物理文件
        trash_path = os.path.join(TRASH_DIR, node.full_path.lstrip('/'))
        if os.path.exists(trash_path):
            if os.path.isfile(trash_path):
                os.remove(trash_path)
            else:
                shutil.rmtree(trash_path)
        
        # 删除数据库记录（级联删除子节点）
        if node.is_directory:
            for child in node.get_all_descendants(include_deleted=True):
                self.db.delete(child)
        
        self.db.delete(node)
        self.db.commit()
        return True
    
    def rename_node(self, node: FileNode, new_name: str) -> bool:
        """重命名文件/目录"""
        if node.is_deleted:
            return False
        
        old_name = node.name
        old_path = node.full_path
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        
        # 检查新路径是否已存在
        if self.get_node_by_path(new_path, node.owner):
            raise ValueError(f"重命名失败：路径 {new_path} 已存在")
        
        # 移动物理文件
        old_physical = node.physical_path
        new_physical = os.path.join(STORAGE_DIR, new_path.lstrip('/'))
        
        if os.path.exists(old_physical):
            os.rename(old_physical, new_physical)
        
        # 更新数据库记录
        node.name = new_name
        node.path = new_path
        node.full_path = new_path
        
        if node.is_file:
            # 更新文件扩展名
            node.file_extension = os.path.splitext(new_name)[1].lower()
        
        # 如果是目录，更新所有子节点的路径
        if node.is_directory:
            self._update_children_paths(node, old_path, new_path)
        
        self.db.commit()
        return True
    
    def _update_children_paths(self, parent: FileNode, old_parent_path: str, new_parent_path: str):
        """递归更新子节点路径"""
        for child in parent.get_all_descendants(include_deleted=True):
            old_child_path = child.full_path
            new_child_path = old_child_path.replace(old_parent_path, new_parent_path, 1)
            
            child.path = new_child_path
            child.full_path = new_child_path
    
    def get_node_info(self, node: FileNode) -> dict:
        """获取节点详细信息"""
        info = {
            'id': node.id,
            'name': node.name,
            'path': node.path,
            'full_path': node.full_path,
            'type': node.node_type,
            'is_deleted': node.is_deleted,
            'created_at': node.created_at.isoformat(),
            'updated_at': node.updated_at.isoformat(),
        }
        
        if node.is_file:
            info.update({
                'size': node.file_size,
                'mime_type': node.mime_type,
                'extension': node.file_extension,
            })
        
        if node.is_deleted and node.deleted_at:
            info['deleted_at'] = node.deleted_at.isoformat()
        
        return info