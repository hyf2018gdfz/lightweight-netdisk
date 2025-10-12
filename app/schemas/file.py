"""
文件相关的Pydantic模式
"""

from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
import os


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    success: bool
    message: str
    file_info: Optional[dict] = None


class DirectoryCreateRequest(BaseModel):
    """创建目录请求"""
    path: str
    
    @validator('path')
    def validate_path(cls, v):
        if not v or not v.strip():
            raise ValueError('路径不能为空')
        
        # 清理路径
        path = v.strip()
        if not path.startswith('/'):
            path = '/' + path
        
        # 标准化路径
        path = os.path.normpath(path)
        
        # 检查路径安全性
        if '..' in path:
            raise ValueError('路径包含非法字符')
        
        return path


class FileNodeResponse(BaseModel):
    """文件节点响应"""
    id: int
    name: str
    path: str
    full_path: str
    type: str
    size: Optional[int] = None
    mime_type: Optional[str] = None
    extension: Optional[str] = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    can_preview: bool = False
    icon: str = "📄"
    # 回收站相关字段
    days_remaining: Optional[int] = None
    will_delete_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class DirectoryListResponse(BaseModel):
    """目录列表响应"""
    path: str
    items: List[FileNodeResponse]
    parent_path: Optional[str] = None


class RenameRequest(BaseModel):
    """重命名请求"""
    new_name: str
    
    @validator('new_name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('新名称不能为空')
        
        # 清理文件名
        name = v.strip()
        
        # 检查非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            if char in name:
                raise ValueError(f'文件名不能包含字符: {char}')
        
        # 检查长度
        if len(name) > 255:
            raise ValueError('文件名过长')
        
        return name


class MoveRequest(BaseModel):
    """移动请求"""
    target_path: str
    
    @validator('target_path')
    def validate_path(cls, v):
        if not v or not v.strip():
            raise ValueError('目标路径不能为空')
        
        path = v.strip()
        if not path.startswith('/'):
            path = '/' + path
        
        path = os.path.normpath(path)
        
        if '..' in path:
            raise ValueError('路径包含非法字符')
        
        return path


class SearchRequest(BaseModel):
    """搜索请求"""
    keyword: str
    path: str = "/"
    include_content: bool = False
    
    @validator('keyword')
    def validate_keyword(cls, v):
        if not v or not v.strip():
            raise ValueError('搜索关键词不能为空')
        return v.strip()
    
    @validator('path')
    def validate_path(cls, v):
        path = v.strip() if v else '/'
        if not path.startswith('/'):
            path = '/' + path
        return os.path.normpath(path)


class SearchResponse(BaseModel):
    """搜索响应"""
    keyword: str
    results: List[FileNodeResponse]
    total: int