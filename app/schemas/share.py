"""
分享系统相关的Pydantic模式
"""

from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime


class CreateShareRequest(BaseModel):
    """创建分享链接请求"""
    file_node_id: int
    password: Optional[str] = None
    expire_hours: Optional[int] = None  # 过期小时数
    max_downloads: Optional[int] = None
    description: Optional[str] = None
    
    @validator('expire_hours')
    def validate_expire_hours(cls, v):
        if v is not None and v <= 0:
            raise ValueError('过期时间必须大于0小时')
        if v is not None and v > 8760:  # 1年
            raise ValueError('过期时间不能超过1年')
        return v
    
    @validator('max_downloads')
    def validate_max_downloads(cls, v):
        if v is not None and v <= 0:
            raise ValueError('最大下载次数必须大于0')
        if v is not None and v > 10000:
            raise ValueError('最大下载次数不能超过10000')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 4:
                raise ValueError('分享密码不能少于4位')
            if len(v) > 20:
                raise ValueError('分享密码不能超过20位')
        return v


class ShareResponse(BaseModel):
    """分享链接响应"""
    share_id: str
    share_url: str
    expire_at: Optional[datetime] = None
    max_downloads: Optional[int] = None
    has_password: bool
    description: Optional[str] = None
    file_info: dict


class ShareInfoResponse(BaseModel):
    """分享信息响应"""
    share_id: str
    file_info: dict
    creator: str
    created_at: datetime
    has_password: bool
    is_expired: bool
    is_download_limit_reached: bool
    current_downloads: int
    max_downloads: Optional[int] = None
    description: Optional[str] = None


class ShareListResponse(BaseModel):
    """分享列表响应"""
    shares: list
    total: int


class ShareAccessRequest(BaseModel):
    """访问分享请求"""
    password: Optional[str] = None


class ShareDeleteRequest(BaseModel):
    """删除分享请求"""
    share_id: str


class UpdateShareRequest(BaseModel):
    """更新分享设置请求"""
    password: Optional[str] = None
    expire_hours: Optional[int] = None
    max_downloads: Optional[int] = None
    description: Optional[str] = None
    
    @validator('expire_hours')
    def validate_expire_hours(cls, v):
        if v is not None and v <= 0:
            raise ValueError('过期时间必须大于0小时')
        if v is not None and v > 8760:  # 1年
            raise ValueError('过期时间不能超过1年')
        return v
    
    @validator('max_downloads')
    def validate_max_downloads(cls, v):
        if v is not None and v <= 0:
            raise ValueError('最大下载次数必须大于0')
        if v is not None and v > 10000:
            raise ValueError('最大下载次数不能超过10000')
        return v