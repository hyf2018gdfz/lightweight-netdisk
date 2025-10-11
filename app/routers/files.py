"""
文件管理相关路由
"""

import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.file import FileNode
from app.services.file_service import FileService
from app.utils.auth import get_current_user
from app.utils.file_utils import (
    get_file_content, get_text_content, create_zip_from_nodes,
    format_file_size, get_file_icon, can_preview, sanitize_filename
)
from app.schemas.file import (
    FileUploadResponse, DirectoryCreateRequest, FileNodeResponse,
    DirectoryListResponse, RenameRequest, MoveRequest,
    SearchRequest, SearchResponse
)
from app.config import MAX_FILE_SIZE
import io

router = APIRouter()


@router.get("/browse", response_model=DirectoryListResponse)
async def browse_directory(
    path: str = Query("/", description="目录路径"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """浏览目录"""
    file_service = FileService(db)
    
    # 获取目录内容
    children = file_service.get_children(path, current_user)
    
    # 转换为响应模型
    items = []
    for child in children:
        item_data = file_service.get_node_info(child)
        item_data['can_preview'] = can_preview(child)
        item_data['icon'] = get_file_icon(child)
        if child.is_file and child.file_size:
            item_data['formatted_size'] = format_file_size(child.file_size)
        items.append(FileNodeResponse(**item_data))
    
    # 计算父目录路径
    parent_path = None
    if path != '/':
        parent_path = os.path.dirname(path)
        if parent_path == '':
            parent_path = '/'
    
    return DirectoryListResponse(
        path=path,
        items=items,
        parent_path=parent_path
    )


@router.post("/upload", response_model=FileUploadResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    path: str = Form("/", description="上传目录路径"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文件"""
    file_service = FileService(db)
    uploaded_files = []
    errors = []
    
    for file in files:
        try:
            # 检查文件大小
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                errors.append(f"{file.filename}: 文件过大")
                continue
            
            # 清理文件名
            filename = sanitize_filename(file.filename or 'unnamed')
            file_path = os.path.join(path, filename)
            
            # 保存文件
            file_node = file_service.save_uploaded_file(file_path, content, current_user)
            file_info = file_service.get_node_info(file_node)
            file_info['formatted_size'] = format_file_size(file_node.file_size)
            uploaded_files.append(file_info)
            
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    if uploaded_files:
        message = f"成功上传 {len(uploaded_files)} 个文件"
        if errors:
            message += f"，{len(errors)} 个文件失败"
        return FileUploadResponse(
            success=True,
            message=message,
            file_info={'uploaded': uploaded_files, 'errors': errors}
        )
    else:
        return FileUploadResponse(
            success=False,
            message=f"上传失败: {'; '.join(errors)}"
        )


@router.post("/mkdir", response_model=FileUploadResponse)
async def create_directory(
    request: DirectoryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建目录"""
    try:
        file_service = FileService(db)
        dir_node = file_service.create_directory(request.path, current_user)
        
        return FileUploadResponse(
            success=True,
            message=f"目录 '{dir_node.name}' 创建成功",
            file_info=file_service.get_node_info(dir_node)
        )
    except Exception as e:
        return FileUploadResponse(
            success=False,
            message=f"创建目录失败: {str(e)}"
        )


@router.get("/download/{node_id}")
async def download_file(
    node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载文件"""
    file_service = FileService(db)
    node = file_service.get_node_by_id(node_id, current_user)
    
    if not node:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if node.is_file:
        # 下载单个文件
        file_path = node.physical_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            file_path,
            filename=node.name,
            media_type='application/octet-stream'
        )
    
    elif node.is_directory:
        # 打包目录为ZIP下载
        children = [node] + node.get_all_descendants()
        zip_content = create_zip_from_nodes(children)
        
        zip_filename = f"{node.name}.zip"
        
        return StreamingResponse(
            io.BytesIO(zip_content),
            media_type='application/zip',
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )


@router.put("/rename/{node_id}")
async def rename_file(
    node_id: int,
    request: RenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重命名文件/目录"""
    try:
        file_service = FileService(db)
        node = file_service.get_node_by_id(node_id, current_user)
        
        if not node:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        old_name = node.name
        file_service.rename_node(node, request.new_name)
        
        return {
            "success": True,
            "message": f"'{old_name}' 重命名为 '{request.new_name}' 成功"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"重命名失败: {str(e)}"
        }


@router.delete("/delete/{node_id}")
async def delete_file(
    node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除文件/目录（移入回收站）"""
    try:
        file_service = FileService(db)
        node = file_service.get_node_by_id(node_id, current_user)
        
        if not node:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if file_service.move_to_trash(node):
            return {
                "success": True,
                "message": f"'{node.name}' 已移入回收站"
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


@router.get("/preview/{node_id}")
async def preview_file(
    node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """预览文件"""
    file_service = FileService(db)
    node = file_service.get_node_by_id(node_id, current_user)
    
    if not node or not node.is_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if not can_preview(node):
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


@router.post("/search", response_model=SearchResponse)
async def search_files(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索文件"""
    # 简单的文件名搜索
    query = db.query(FileNode).filter(
        FileNode.owner_id == current_user.id,
        FileNode.is_deleted == False,
        FileNode.name.contains(request.keyword)
    )
    
    # 如果指定了路径，只在该路径下搜索
    if request.path != '/':
        query = query.filter(FileNode.full_path.startswith(request.path))
    
    results = query.limit(100).all()
    
    # 转换为响应模型
    file_service = FileService(db)
    items = []
    for node in results:
        item_data = file_service.get_node_info(node)
        item_data['can_preview'] = can_preview(node)
        item_data['icon'] = get_file_icon(node)
        items.append(FileNodeResponse(**item_data))
    
    return SearchResponse(
        keyword=request.keyword,
        results=items,
        total=len(items)
    )