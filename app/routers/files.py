"""
文件管理相关路由
"""

import os
from typing import List
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
import json
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.file import FileNode
from app.services.file_service import FileService
from app.services.chunk_upload_service import ChunkUploadService
from app.utils.auth import get_current_user
from app.utils.file_utils import (
    get_file_content, get_text_content, create_zip_from_nodes,
    format_file_size, get_file_icon, can_preview, sanitize_filename,
    is_audio, is_video
)
from app.schemas.file import (
    FileUploadResponse, DirectoryCreateRequest, FileNodeResponse,
    DirectoryListResponse, RenameRequest, MoveRequest,
    SearchRequest, SearchResponse, BatchDownloadRequest,
    ChunkUploadInitRequest, ChunkUploadInitResponse,
    ChunkUploadRequest, ChunkUploadResponse,
    ChunkUploadCompleteRequest, ChunkUploadCompleteResponse
)
from app.config import MAX_FILE_SIZE
import io

router = APIRouter()


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


@router.get("/browse", response_model=DirectoryListResponse)
async def browse_directory(
    path: str = Query("/", description="目录路径"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """浏览目录"""
    file_service = FileService(db)
    
    # 验证目录是否存在（除了根目录）
    if path != "/":
        parent_node = file_service.get_node_by_path(path, current_user)
        if not parent_node:
            raise HTTPException(status_code=404, detail=f"目录不存在: {path}")
        if not parent_node.is_directory:
            raise HTTPException(status_code=400, detail=f"路径不是目录: {path}")
    
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
    relative_paths: str = Form("", description="文件相对路径，用于文件夹上传"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文件"""
    file_service = FileService(db)
    uploaded_files = []
    errors = []
    
    # 解析相对路径
    relative_path_list = []
    if relative_paths:
        try:
            import json
            relative_path_list = json.loads(relative_paths)
        except:
            relative_path_list = []
    
    for i, file in enumerate(files):
        try:
            # 检查文件大小
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                errors.append(f"{file.filename}: 文件过大")
                continue
            
            # 处理文件路径
            if i < len(relative_path_list) and relative_path_list[i]:
                # 文件夹上传，使用相对路径
                relative_path = relative_path_list[i]
                # 清理并标准化路径
                relative_path = os.path.normpath(relative_path)
                # 确保目录分隔符一致
                relative_path = relative_path.replace('\\', '/')
                # 组合完整路径
                if path == '/':
                    file_path = '/' + relative_path
                else:
                    file_path = path + '/' + relative_path
            else:
                # 普通文件上传
                filename = sanitize_filename(file.filename or 'unnamed')
                file_path = os.path.join(path, filename)
            
            # 确保所有必要的目录都存在
            dir_path = os.path.dirname(file_path)
            if dir_path and dir_path != '/':
                file_service.ensure_directory_exists(dir_path, current_user)
            
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
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载文件（支持断点续传）"""
    file_service = FileService(db)
    node = file_service.get_node_by_id(node_id, current_user)
    
    if not node:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if node.is_file:
        # 下载单个文件（支持Range请求）
        file_path = node.physical_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        file_size = os.path.getsize(file_path)
        range_header = request.headers.get('Range')
        
        if range_header:
            # 处理Range请求
            try:
                ranges = range_header.replace('bytes=', '').split('-')
                start = int(ranges[0]) if ranges[0] else 0
                end = int(ranges[1]) if ranges[1] else file_size - 1
                
                # 验证范围
                if start >= file_size or end >= file_size or start > end:
                    raise HTTPException(status_code=416, detail="Range Not Satisfiable")
                
                content_length = end - start + 1
                
                def iterfile(start: int, end: int):
                    with open(file_path, 'rb') as file:
                        file.seek(start)
                        remaining = end - start + 1
                        while remaining > 0:
                            chunk_size = min(8192, remaining)
                            chunk = file.read(chunk_size)
                            if not chunk:
                                break
                            remaining -= len(chunk)
                            yield chunk
                
                headers = {
                    'Content-Range': f'bytes {start}-{end}/{file_size}',
                    'Accept-Ranges': 'bytes',
                    'Content-Length': str(content_length),
                    'Content-Disposition': encode_filename_for_content_disposition(node.name)
                }
                
                return StreamingResponse(
                    iterfile(start, end),
                    status_code=206,
                    headers=headers,
                    media_type='application/octet-stream'
                )
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid Range header")
        else:
            # 普通下载
            headers = {
                'Accept-Ranges': 'bytes',
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
        elif is_audio(node):
            # 音频文件直接返回
            audio_mime_types = {
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.flac': 'audio/flac',
                '.aac': 'audio/aac',
                '.ogg': 'audio/ogg',
                '.m4a': 'audio/mp4'
            }
            mime_type = audio_mime_types.get(node.file_extension, 'audio/mpeg')
            return FileResponse(
                node.physical_path,
                media_type=mime_type,
                filename=node.name
            )
        elif is_video(node):
            # 视频文件直接返回
            video_mime_types = {
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo',
                '.mkv': 'video/x-matroska',
                '.mov': 'video/quicktime',
                '.wmv': 'video/x-ms-wmv',
                '.webm': 'video/webm',
                '.m4v': 'video/mp4'
            }
            mime_type = video_mime_types.get(node.file_extension, 'video/mp4')
            return FileResponse(
                node.physical_path,
                media_type=mime_type,
                filename=node.name
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的预览类型")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")


@router.get("/search", response_model=SearchResponse)
async def search_files(
    keyword: str = Query(..., description="搜索关键词"),
    path: str = Query("/", description="搜索路径"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索文件"""
    # 简单的文件名搜索
    query = db.query(FileNode).filter(
        FileNode.owner_id == current_user.id,
        FileNode.is_deleted == False,
        FileNode.name.contains(keyword)
    )
    
    # 如果指定了路径，只在该路径下搜索
    if path != '/':
        query = query.filter(FileNode.full_path.startswith(path))
    
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
        keyword=keyword,
        results=items,
        total=len(items)
    )


@router.post("/download/batch")
async def batch_download(
    request: BatchDownloadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量下载文件（ZIP打包）"""
    file_service = FileService(db)
    
    # 获取所有文件节点
    nodes = []
    for file_id in request.file_ids:
        node = file_service.get_node_by_id(file_id, current_user)
        if node:
            nodes.append(node)
    
    if not nodes:
        raise HTTPException(status_code=404, detail="没有找到指定的文件")
    
    # 生成ZIP文件
    try:
        zip_content = create_zip_from_nodes(nodes)
        
        # 生成ZIP文件名
        if len(nodes) == 1:
            zip_filename = f"{nodes[0].name}.zip"
        else:
            zip_filename = f"batch_download_{len(nodes)}_files.zip"
        
        return StreamingResponse(
            io.BytesIO(zip_content),
            media_type='application/zip',
            headers={"Content-Disposition": encode_filename_for_content_disposition(zip_filename)}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"打包失败: {str(e)}")


# 分片上传相关端点

@router.post("/chunk/init", response_model=ChunkUploadInitResponse)
async def init_chunk_upload(
    request: ChunkUploadInitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """初始化分片上传"""
    try:
        chunk_service = ChunkUploadService(db)
        upload_id, total_chunks, uploaded_chunks = chunk_service.init_chunk_upload(
            request.filename,
            request.file_size,
            request.chunk_size,
            request.path,
            current_user,
            request.file_hash
        )
        
        return ChunkUploadInitResponse(
            success=True,
            message="分片上传初始化成功",
            upload_id=upload_id,
            total_chunks=total_chunks,
            uploaded_chunks=uploaded_chunks
        )
        
    except Exception as e:
        return ChunkUploadInitResponse(
            success=False,
            message=f"初始化失败: {str(e)}"
        )


@router.post("/chunk/upload", response_model=ChunkUploadResponse)
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    chunk_hash: str = Form(""),
    chunk_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传单个分片"""
    try:
        chunk_service = ChunkUploadService(db)
        
        # 读取分片数据
        chunk_data = await chunk_file.read()
        
        # 上传分片
        success = chunk_service.upload_chunk(
            upload_id,
            chunk_index,
            chunk_data,
            current_user,
            chunk_hash if chunk_hash else None
        )
        
        return ChunkUploadResponse(
            success=success,
            message="分片上传成功",
            chunk_index=chunk_index,
            received=True
        )
        
    except Exception as e:
        return ChunkUploadResponse(
            success=False,
            message=f"分片上传失败: {str(e)}",
            chunk_index=chunk_index,
            received=False
        )


@router.post("/chunk/complete", response_model=ChunkUploadCompleteResponse)
async def complete_chunk_upload(
    request: ChunkUploadCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """完成分片上传"""
    try:
        chunk_service = ChunkUploadService(db)
        
        # 完成上传
        file_info = chunk_service.complete_chunk_upload(
            request.upload_id,
            current_user,
            request.file_hash
        )
        
        return ChunkUploadCompleteResponse(
            success=True,
            message="文件上传完成",
            file_info=file_info
        )
        
    except Exception as e:
        return ChunkUploadCompleteResponse(
            success=False,
            message=f"完成上传失败: {str(e)}"
        )


@router.get("/chunk/status/{upload_id}")
async def get_chunk_upload_status(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取分片上传状态"""
    try:
        chunk_service = ChunkUploadService(db)
        status = chunk_service.get_upload_status(upload_id, current_user)
        return {"success": True, "data": status}
        
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.delete("/chunk/cancel/{upload_id}")
async def cancel_chunk_upload(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消分片上传"""
    try:
        chunk_service = ChunkUploadService(db)
        success = chunk_service.cancel_upload(upload_id, current_user)
        
        if success:
            return {"success": True, "message": "上传已取消"}
        else:
            return {"success": False, "message": "上传会话不存在"}
            
    except Exception as e:
        return {"success": False, "message": str(e)}