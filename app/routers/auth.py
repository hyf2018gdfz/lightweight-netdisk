"""
认证相关路由
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo, ChangePasswordRequest
from app.utils.auth import (
    authenticate_user, 
    create_access_token, 
    get_current_user,
    get_current_user_optional
)
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login")
async def login_page(request: Request):
    """登录页面"""
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "title": "登录 - 个人网盘系统"
    })


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录"""
    # 验证用户
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()
    
    return LoginResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 转换为秒
        user_info={
            "id": user.id,
            "username": user.username,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    )


@router.post("/logout")
async def logout():
    """用户登出"""
    # JWT无状态，登出只需在前端删除token
    return {"message": "登出成功"}


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return UserInfo.from_orm(current_user)


@router.put("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    # 验证当前密码
    if not current_user.verify_password(password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 更新密码
    current_user.hashed_password = User.hash_password(password_data.new_password)
    db.commit()
    
    return {"message": "密码修改成功"}


@router.get("/check")
async def check_auth(
    request: Request,
    db: Session = Depends(get_db)
):
    """检查认证状态"""
    user = get_current_user_optional(request, db)
    if user:
        return {
            "authenticated": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "is_active": user.is_active
            }
        }
    else:
        return {"authenticated": False}