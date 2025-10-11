"""
认证相关的Pydantic模式
"""

from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str
    
    @validator('username')
    def username_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()
    
    @validator('password')
    def password_must_not_be_empty(cls, v):
        if not v or len(v) < 3:
            raise ValueError('密码不能少于3位')
        return v


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 过期时间（秒）
    user_info: dict


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def password_validation(cls, v):
        if len(v) < 6:
            raise ValueError('新密码不能少于6位')
        return v