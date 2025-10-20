"""
分享系统相关路由
"""

import os
from typing import List, Optional
from datetime import datetime, timedelta
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.file import FileNode
from app.models.share import ShareLink
from app.services.file_service import FileService
from app.utils.auth import get_current_user, get_current_user_optional
from app.utils.file_utils import (
    get_file_content, get_text_content, create_zip_from_nodes,
    format_file_size, get_file_icon, can_preview
)
from app.schemas.share import (
    CreateShareRequest, ShareResponse, ShareInfoResponse, ShareListResponse,
    ShareAccessRequest, ShareDeleteRequest, UpdateShareRequest
)
import io

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def encode_filename_for_content_disposition(filename: str) -> str:
    """
    Encode filename for Content-Disposition header to support special characters
    Uses RFC 5987 / RFC 2231 encoding
    """
    try:
        # Try ASCII first
        filename.encode('ascii')
        # If it's pure ASCII, use simple format
        return f'attachment; filename="{filename}"'
    except UnicodeEncodeError:
        # Use RFC 5987 format for non-ASCII characters
        encoded_filename = quote(filename.encode('utf-8'))
        return f"attachment; filename*=UTF-8''{encoded_filename}"


@router.post("/create", response_model=ShareResponse)
async def create_share(
    request: CreateShareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建分享链接"""
    try:
        file_service = FileService(db)
        
        # 获取文件节点
        node = file_service.get_node_by_id(request.file_node_id, current_user)
        if not node:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 检查是否已存在有效的分享链接
        existing_share = db.query(ShareLink).filter(
            ShareLink.file_node_id == request.file_node_id,
            ShareLink.creator_id == current_user.id,
            ShareLink.is_active == True
        ).first()
        
        # 如果已存在有效的分享链接，直接返回
        if existing_share and existing_share.is_accessible:
            return ShareResponse(
                share_id=existing_share.share_id,
                share_url=f"/share/{existing_share.share_id}",
                expire_at=existing_share.expire_at,
                max_downloads=existing_share.max_downloads,
                has_password=existing_share.password is not None,
                description=existing_share.description,
                file_info=file_service.get_node_info(node)
            )
        
        # 生成唆一分享 ID
        share_id = ShareLink.generate_share_id()
        while db.query(ShareLink).filter(ShareLink.share_id == share_id).first():
            share_id = ShareLink.generate_share_id()
        
        # 计算过期时间
        expire_at = None
        if request.expire_hours:
            expire_at = datetime.utcnow() + timedelta(hours=request.expire_hours)
        
        # 创建分享链接
        share_link = ShareLink(
            share_id=share_id,
            file_node_id=request.file_node_id,
            creator_id=current_user.id,
            expire_at=expire_at,
            max_downloads=request.max_downloads,
            description=request.description
        )
        
        # 设置密码
        if request.password:
            share_link.set_password(request.password)
        
        db.add(share_link)
        db.commit()
        db.refresh(share_link)
        
        # 构建分享 URL
        share_url = f"/share/{share_id}"
        
        return ShareResponse(
            share_id=share_id,
            share_url=share_url,
            expire_at=share_link.expire_at,
            max_downloads=share_link.max_downloads,
            has_password=share_link.password is not None,
            description=share_link.description,
            file_info=file_service.get_node_info(node)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建分享链接失败: {str(e)}")


@router.get("/list", response_model=ShareListResponse)
async def list_shares(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的分享链接列表"""
    shares = db.query(ShareLink).filter(
        ShareLink.creator_id == current_user.id
    ).order_by(ShareLink.created_at.desc()).all()
    
    file_service = FileService(db)
    share_list = []
    
    for share in shares:
        file_info = file_service.get_node_info(share.file_node) if share.file_node else None
        share_data = {
            'share_id': share.share_id,
            'share_url': f"/share/{share.share_id}",
            'file_info': file_info,
            'created_at': share.created_at,
            'expire_at': share.expire_at,
            'max_downloads': share.max_downloads,
            'current_downloads': share.current_downloads,
            'has_password': share.password is not None,
            'is_active': share.is_active,
            'is_expired': share.is_expired,
            'is_accessible': share.is_accessible,
            'description': share.description,
            'last_accessed': share.last_accessed
        }
        share_list.append(share_data)
    
    return ShareListResponse(
        shares=share_list,
        total=len(share_list)
    )


@router.get("/{share_id}")
async def access_share_page(
    share_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """访问分享页面"""
    # 查找分享链接
    share_link = db.query(ShareLink).filter(ShareLink.share_id == share_id).first()
    
    if not share_link:
        return templates.TemplateResponse("share/not_found.html", {
            "request": request,
            "message": "分享链接不存在"
        })
    
    if not share_link.is_accessible:
        reason = "分享链接已过期" if share_link.is_expired else "下载次数已用完"
        return templates.TemplateResponse("share/expired.html", {
            "request": request,
            "message": reason
        })
    
    file_service = FileService(db)
    file_info = file_service.get_node_info(share_link.file_node)
    file_info['icon'] = get_file_icon(share_link.file_node)
    file_info['can_preview'] = can_preview(share_link.file_node)
    if share_link.file_node.is_file and share_link.file_node.file_size:
        file_info['formatted_size'] = format_file_size(share_link.file_node.file_size)
    
    return templates.TemplateResponse("share/access.html", {
        "request": request,
        "share": {
            "share_id": share_link.share_id,
            "has_password": share_link.password is not None,
            "description": share_link.description,
            "creator": share_link.creator.username,
            "created_at": share_link.created_at,
            "expire_at": share_link.expire_at,
            "current_downloads": share_link.current_downloads,
            "max_downloads": share_link.max_downloads
        },
        "file": file_info
    })


@router.post("/{share_id}/access")
async def verify_share_access(
    share_id: str,
    access_request: ShareAccessRequest,
    db: Session = Depends(get_db)
):
    """验证分享访问权限"""
    share_link = db.query(ShareLink).filter(ShareLink.share_id == share_id).first()
    
    if not share_link or not share_link.is_accessible:
        raise HTTPException(status_code=404, detail="分享链接不可用")
    
    # 验证密码
    if not share_link.verify_password(access_request.password or ""):
        raise HTTPException(status_code=401, detail="密码错误")
    
    return {"success": True, "message": "验证成功"}


@router.get("/{share_id}/download")
async def download_shared_file(
    share_id: str,
    password: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """下载分享文件"""
    share_link = db.query(ShareLink).filter(ShareLink.share_id == share_id).first()
    
    if not share_link or not share_link.is_accessible:
        raise HTTPException(status_code=404, detail="分享链接不可用")
    
    # 验证密码
    if not share_link.verify_password(password or ""):
        raise HTTPException(status_code=401, detail="密码错误")
    
    node = share_link.file_node
    
    # 增加下载计数
    share_link.increment_download_count()
    db.commit()
    
    if node.is_file:
        # 下载单个文件
        file_path = node.physical_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        headers = {
            'Content-Disposition': encode_filename_for_content_disposition(node.name)
        }
        return FileResponse(
            file_path,
            media_type='application/octet-stream',
            headers=headers
        )
    
    elif node.is_directory:
        # 打包目录为ZIP下载
        children = [node] + node.get_all_descendants()
        zip_content = create_zip_from_nodes(children)
        
        zip_filename = f"{node.name}.zip"
        
        return StreamingResponse(
            io.BytesIO(zip_content),
            media_type='application/zip',
            headers={"Content-Disposition": encode_filename_for_content_disposition(zip_filename)}
        )


@router.get("/{share_id}/preview")
async def preview_shared_file(
    share_id: str,
    password: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """预览分享文件"""
    share_link = db.query(ShareLink).filter(ShareLink.share_id == share_id).first()
    
    if not share_link or not share_link.is_accessible:
        raise HTTPException(status_code=404, detail="分享链接不可用")
    
    # 验证密码
    if not share_link.verify_password(password or ""):
        raise HTTPException(status_code=401, detail="密码错误")
    
    node = share_link.file_node
    
    if not node.is_file or not can_preview(node):
        raise HTTPException(status_code=400, detail="文件不支持预览")
    
    try:
        if node.mime_type and node.mime_type.startswith('image/'):
            # 图片文件直接返回
            return FileResponse(
                node.physical_path,
                media_type=node.mime_type,
                filename=node.name
            )
        elif node.file_extension in ['.txt', '.md', '.json', '.xml', '.html', '.css', '.js', '.py']:
            # 文本文件返回JSON
            content = get_text_content(node)
            return {
                "type": "text",
                "content": content,
                "filename": node.name,
                "size": node.file_size
            }
        elif node.file_extension == '.pdf':
            # PDF文件直接返回
            return FileResponse(
                node.physical_path,
                media_type='application/pdf',
                filename=node.name
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的预览类型")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")


@router.put("/{share_id}")
async def update_share(
    share_id: str,
    update_request: UpdateShareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新分享链接设置"""
    share_link = db.query(ShareLink).filter(
        ShareLink.share_id == share_id,
        ShareLink.creator_id == current_user.id
    ).first()
    
    if not share_link:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    
    try:
        # 更新密码
        if update_request.password is not None:
            if update_request.password:
                share_link.set_password(update_request.password)
            else:
                share_link.password = None
        
        # 更新过期时间
        if update_request.expire_hours is not None:
            if update_request.expire_hours > 0:
                share_link.expire_at = datetime.utcnow() + timedelta(hours=update_request.expire_hours)
            else:
                share_link.expire_at = None
        
        # 更新下载次数限制
        if update_request.max_downloads is not None:
            share_link.max_downloads = update_request.max_downloads
        
        # 更新描述
        if update_request.description is not None:
            share_link.description = update_request.description
        
        db.commit()
        
        return {
            "success": True,
            "message": "分享链接更新成功"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"更新失败: {str(e)}"
        }


@router.delete("/{share_id}")
async def delete_share(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除分享链接"""
    share_link = db.query(ShareLink).filter(
        ShareLink.share_id == share_id,
        ShareLink.creator_id == current_user.id
    ).first()
    
    if not share_link:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    
    try:
        db.delete(share_link)
        db.commit()
        
        return {
            "success": True,
            "message": "分享链接已删除"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"删除失败: {str(e)}"
        }


@router.get("/{share_id}/info", response_model=ShareInfoResponse)
async def get_share_info(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取分享链接信息"""
    share_link = db.query(ShareLink).filter(
        ShareLink.share_id == share_id,
        ShareLink.creator_id == current_user.id
    ).first()
    
    if not share_link:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    
    file_service = FileService(db)
    file_info = file_service.get_node_info(share_link.file_node)
    
    return ShareInfoResponse(
        share_id=share_link.share_id,
        file_info=file_info,
        creator=share_link.creator.username,
        created_at=share_link.created_at,
        has_password=share_link.password is not None,
        is_expired=share_link.is_expired,
        is_download_limit_reached=share_link.is_download_limit_reached,
        current_downloads=share_link.current_downloads,
        max_downloads=share_link.max_downloads,
        description=share_link.description
    )