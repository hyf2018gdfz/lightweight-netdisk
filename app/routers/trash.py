"""
回收站相关路由
"""

from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.file import FileNode
from app.services.file_service import FileService
from app.utils.auth import get_current_user
from app.utils.file_utils import get_file_icon, can_preview, format_file_size
from app.schemas.file import FileNodeResponse, DirectoryListResponse
from app.config import TRASH_RETENTION_DAYS

router = APIRouter()


@router.get("/list", response_model=DirectoryListResponse)
async def list_trash(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取回收站文件列表"""
    # 查询用户顶级删除的文件（只显示没有被删除父目录的项目）
    deleted_files = db.query(FileNode).filter(
        FileNode.owner_id == current_user.id,
        FileNode.is_deleted == True
    ).all()
    
    # 过滤出顶级删除项目（没有被删除的父目录）
    top_level_deleted = []
    for node in deleted_files:
        # 检查是否有被删除的父目录
        has_deleted_parent = False
        current = node.parent
        while current:
            if current.is_deleted:
                has_deleted_parent = True
                break
            current = current.parent
        
        if not has_deleted_parent:
            top_level_deleted.append(node)
    
    # 按删除时间排序
    top_level_deleted.sort(key=lambda x: x.deleted_at, reverse=True)
    deleted_files = top_level_deleted
    
    # 转换为响应模型
    file_service = FileService(db)
    items = []
    for node in deleted_files:
        item_data = file_service.get_node_info(node)
        item_data['can_preview'] = can_preview(node)
        item_data['icon'] = get_file_icon(node)
        if node.is_file and node.file_size:
            item_data['formatted_size'] = format_file_size(node.file_size)
        
        # 计算剩余天数
        if node.deleted_at:
            days_since_deleted = (datetime.utcnow() - node.deleted_at).days
            days_remaining = TRASH_RETENTION_DAYS - days_since_deleted
            item_data['days_remaining'] = max(0, days_remaining)
            item_data['will_delete_at'] = (node.deleted_at + timedelta(days=TRASH_RETENTION_DAYS)).isoformat()
        
        items.append(FileNodeResponse(**item_data))
    
    return DirectoryListResponse(
        path="/trash",
        items=items,
        parent_path=None
    )


@router.post("/restore/{node_id}")
async def restore_file(
    node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从回收站恢复文件"""
    try:
        file_service = FileService(db)
        node = file_service.get_node_by_id(node_id, current_user, include_deleted=True)
        
        if not node:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not node.is_deleted:
            raise HTTPException(status_code=400, detail="文件不在回收站中")
        
        if file_service.restore_from_trash(node):
            return {
                "success": True,
                "message": f"'{node.name}' 恢复成功"
            }
        else:
            return {
                "success": False,
                "message": "恢复失败"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"恢复失败: {str(e)}"
        }


@router.delete("/permanent/{node_id}")
async def permanent_delete(
    node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """永久删除文件"""
    try:
        file_service = FileService(db)
        node = file_service.get_node_by_id(node_id, current_user, include_deleted=True)
        
        if not node:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not node.is_deleted:
            raise HTTPException(status_code=400, detail="文件不在回收站中")
        
        if file_service.permanent_delete(node):
            return {
                "success": True,
                "message": f"'{node.name}' 已永久删除"
            }
        else:
            return {
                "success": False,
                "message": "删除失败"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"删除失败: {str(e)}"
        }


@router.post("/empty")
async def empty_trash(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清空回收站"""
    try:
        file_service = FileService(db)
        
        # 获取所有已删除的文件
        deleted_files = db.query(FileNode).filter(
            FileNode.owner_id == current_user.id,
            FileNode.is_deleted == True
        ).all()
        
        success_count = 0
        error_count = 0
        
        for node in deleted_files:
            try:
                if file_service.permanent_delete(node):
                    success_count += 1
                else:
                    error_count += 1
            except Exception:
                error_count += 1
        
        if error_count == 0:
            return {
                "success": True,
                "message": f"回收站已清空，删除了 {success_count} 个项目"
            }
        else:
            return {
                "success": True,
                "message": f"回收站清理完成，删除了 {success_count} 个项目，{error_count} 个项目删除失败"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"清空回收站失败: {str(e)}"
        }


@router.post("/auto-clean")
async def auto_clean_trash(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """自动清理过期文件"""
    try:
        file_service = FileService(db)
        
        # 计算过期时间
        expire_date = datetime.utcnow() - timedelta(days=TRASH_RETENTION_DAYS)
        
        # 查询过期的已删除文件
        expired_files = db.query(FileNode).filter(
            FileNode.owner_id == current_user.id,
            FileNode.is_deleted == True,
            FileNode.deleted_at <= expire_date
        ).all()
        
        success_count = 0
        error_count = 0
        
        for node in expired_files:
            try:
                if file_service.permanent_delete(node):
                    success_count += 1
                else:
                    error_count += 1
            except Exception:
                error_count += 1
        
        if success_count > 0:
            return {
                "success": True,
                "message": f"自动清理完成，删除了 {success_count} 个过期文件"
            }
        else:
            return {
                "success": True,
                "message": "没有过期文件需要清理"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"自动清理失败: {str(e)}"
        }