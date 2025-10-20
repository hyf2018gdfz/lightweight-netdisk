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


class BatchDownloadRequest(BaseModel):
    """批量下载请求"""
    file_ids: List[int]
    
    @validator('file_ids')
    def validate_file_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('文件ID列表不能为空')
        if len(v) > 100:  # 限制最多100个文件
            raise ValueError('一次最多可下载100个文件')
        return v


class FileMetadata(BaseModel):
    """文件元数据"""
    lastModified: Optional[int] = None  # 文件最后修改时间戳
    originalName: Optional[str] = None
    size: Optional[int] = None


class ChunkUploadInitRequest(BaseModel):
    """分片上传初始化请求"""
    filename: str
    file_size: int
    chunk_size: int
    path: str = "/"
    file_hash: Optional[str] = None  # 文件MD5哈希，用于校验
    file_metadata: Optional[FileMetadata] = None  # 文件元数据
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v or not v.strip():
            raise ValueError('文件名不能为空')
        
        # 检查非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            if char in v:
                raise ValueError(f'文件名不能包含字符: {char}')
        
        return v.strip()
    
    @validator('file_size')
    def validate_file_size(cls, v):
        if v <= 0:
            raise ValueError('文件大小必须大于0')
        if v > 10 * 1024 * 1024 * 1024:  # 限制10GB
            raise ValueError('文件大小超过限制（10GB）')
        return v
    
    @validator('chunk_size')
    def validate_chunk_size(cls, v):
        if v <= 0:
            raise ValueError('分片大小必须大于0')
        if v > 50 * 1024 * 1024:  # 限制50MB per chunk
            raise ValueError('分片大小超过限制（50MB）')
        return v


class ChunkUploadInitResponse(BaseModel):
    """分片上传初始化响应"""
    success: bool
    message: str
    upload_id: Optional[str] = None
    total_chunks: Optional[int] = None
    uploaded_chunks: Optional[List[int]] = None  # 已上传的分片索引


class ChunkUploadRequest(BaseModel):
    """分片上传请求"""
    upload_id: str
    chunk_index: int
    chunk_hash: Optional[str] = None  # 分片MD5哈希
    
    @validator('chunk_index')
    def validate_chunk_index(cls, v):
        if v < 0:
            raise ValueError('分片索引不能为负数')
        return v


class ChunkUploadResponse(BaseModel):
    """分片上传响应"""
    success: bool
    message: str
    chunk_index: int
    received: bool = False


class ChunkUploadCompleteRequest(BaseModel):
    """分片上传完成请求"""
    upload_id: str
    file_hash: Optional[str] = None  # 用于最终校验


class ChunkUploadCompleteResponse(BaseModel):
    """分片上传完成响应"""
    success: bool
    message: str
    file_info: Optional[dict] = None