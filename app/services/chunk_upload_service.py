"""
分片上传服务
"""

import os
import uuid
import hashlib
import json
import tempfile
import shutil
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.file_service import FileService
from app.utils.file_utils import sanitize_filename, is_safe_path


class ChunkUploadService:
    """分片上传服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.file_service = FileService(db)
        # 使用临时目录存储分片上传信息
        self.upload_dir = os.path.join(tempfile.gettempdir(), "netdisk_uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def init_chunk_upload(self, filename: str, file_size: int, chunk_size: int, 
                         path: str, user: User, file_hash: Optional[str] = None) -> Tuple[str, int, List[int]]:
        """初始化分片上传"""
        # 生成上传ID
        upload_id = str(uuid.uuid4())
        
        # 计算总分片数
        total_chunks = (file_size + chunk_size - 1) // chunk_size
        
        # 创建上传目录
        upload_path = os.path.join(self.upload_dir, upload_id)
        os.makedirs(upload_path, exist_ok=True)
        
        # 保存上传元数据
        metadata = {
            "upload_id": upload_id,
            "filename": sanitize_filename(filename),
            "file_size": file_size,
            "chunk_size": chunk_size,
            "total_chunks": total_chunks,
            "path": path,
            "user_id": user.id,
            "file_hash": file_hash,
            "created_at": datetime.now().isoformat(),
            "uploaded_chunks": [],
            "status": "uploading"
        }
        
        metadata_file = os.path.join(upload_path, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return upload_id, total_chunks, []
    
    def upload_chunk(self, upload_id: str, chunk_index: int, chunk_data: bytes, 
                    user: User, chunk_hash: Optional[str] = None) -> bool:
        """上传单个分片"""
        upload_path = os.path.join(self.upload_dir, upload_id)
        metadata_file = os.path.join(upload_path, "metadata.json")
        
        if not os.path.exists(metadata_file):
            raise ValueError("上传会话不存在")
        
        # 读取元数据
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 验证用户权限
        if metadata["user_id"] != user.id:
            raise ValueError("无权限访问此上传会话")
        
        # 检查分片索引
        if chunk_index < 0 or chunk_index >= metadata["total_chunks"]:
            raise ValueError("分片索引无效")
        
        # 验证分片哈希（如果提供）
        if chunk_hash:
            actual_hash = hashlib.md5(chunk_data).hexdigest()
            if actual_hash != chunk_hash:
                raise ValueError("分片数据校验失败")
        
        # 保存分片
        chunk_file = os.path.join(upload_path, f"chunk_{chunk_index}")
        with open(chunk_file, 'wb') as f:
            f.write(chunk_data)
        
        # 更新元数据
        if chunk_index not in metadata["uploaded_chunks"]:
            metadata["uploaded_chunks"].append(chunk_index)
        metadata["uploaded_chunks"].sort()
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return True
    
    def complete_chunk_upload(self, upload_id: str, user: User, 
                            file_hash: Optional[str] = None) -> dict:
        """完成分片上传，合并文件"""
        upload_path = os.path.join(self.upload_dir, upload_id)
        metadata_file = os.path.join(upload_path, "metadata.json")
        
        if not os.path.exists(metadata_file):
            raise ValueError("上传会话不存在")
        
        # 读取元数据
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 验证用户权限
        if metadata["user_id"] != user.id:
            raise ValueError("无权限访问此上传会话")
        
        # 检查所有分片是否都已上传
        expected_chunks = list(range(metadata["total_chunks"]))
        if set(metadata["uploaded_chunks"]) != set(expected_chunks):
            missing_chunks = set(expected_chunks) - set(metadata["uploaded_chunks"])
            raise ValueError(f"缺少分片: {list(missing_chunks)}")
        
        # 合并分片
        temp_file = os.path.join(upload_path, "merged_file")
        with open(temp_file, 'wb') as output_file:
            for chunk_index in range(metadata["total_chunks"]):
                chunk_file = os.path.join(upload_path, f"chunk_{chunk_index}")
                if os.path.exists(chunk_file):
                    with open(chunk_file, 'rb') as chunk_f:
                        output_file.write(chunk_f.read())
                else:
                    raise ValueError(f"分片文件缺失: chunk_{chunk_index}")
        
        # 验证合并后的文件大小
        merged_size = os.path.getsize(temp_file)
        if merged_size != metadata["file_size"]:
            raise ValueError(f"合并后文件大小不匹配: 期望 {metadata['file_size']}, 实际 {merged_size}")
        
        # 验证文件哈希（如果提供）
        if file_hash or metadata.get("file_hash"):
            with open(temp_file, 'rb') as f:
                actual_hash = hashlib.md5(f.read()).hexdigest()
            expected_hash = file_hash or metadata["file_hash"]
            if actual_hash != expected_hash:
                raise ValueError("文件完整性校验失败")
        
        # 保存到文件系统
        try:
            with open(temp_file, 'rb') as f:
                file_content = f.read()
            
            # 构建文件路径
            file_path = os.path.join(metadata["path"], metadata["filename"])
            
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path and dir_path != '/':
                self.file_service.ensure_directory_exists(dir_path, user)
            
            # 保存文件
            file_node = self.file_service.save_uploaded_file(file_path, file_content, user)
            
            # 更新元数据状态
            metadata["status"] = "completed"
            metadata["completed_at"] = datetime.now().isoformat()
            metadata["file_id"] = file_node.id
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 获取文件信息
            file_info = self.file_service.get_node_info(file_node)
            
            # 清理临时文件（延迟清理，防止并发问题）
            self._schedule_cleanup(upload_path)
            
            return file_info
            
        except Exception as e:
            # 标记为失败
            metadata["status"] = "failed"
            metadata["error"] = str(e)
            metadata["failed_at"] = datetime.now().isoformat()
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            raise e
    
    def get_upload_status(self, upload_id: str, user: User) -> dict:
        """获取上传状态"""
        upload_path = os.path.join(self.upload_dir, upload_id)
        metadata_file = os.path.join(upload_path, "metadata.json")
        
        if not os.path.exists(metadata_file):
            raise ValueError("上传会话不存在")
        
        # 读取元数据
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 验证用户权限
        if metadata["user_id"] != user.id:
            raise ValueError("无权限访问此上传会话")
        
        return {
            "upload_id": upload_id,
            "filename": metadata["filename"],
            "file_size": metadata["file_size"],
            "total_chunks": metadata["total_chunks"],
            "uploaded_chunks": metadata["uploaded_chunks"], 
            "progress": len(metadata["uploaded_chunks"]) / metadata["total_chunks"] * 100,
            "status": metadata["status"]
        }
    
    def cancel_upload(self, upload_id: str, user: User) -> bool:
        """取消上传"""
        upload_path = os.path.join(self.upload_dir, upload_id)
        metadata_file = os.path.join(upload_path, "metadata.json")
        
        if not os.path.exists(metadata_file):
            return False
        
        # 读取元数据
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 验证用户权限
        if metadata["user_id"] != user.id:
            raise ValueError("无权限访问此上传会话")
        
        # 标记为取消
        metadata["status"] = "cancelled"
        metadata["cancelled_at"] = datetime.now().isoformat()
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 清理文件
        self._schedule_cleanup(upload_path)
        
        return True
    
    def _schedule_cleanup(self, upload_path: str, delay_minutes: int = 5):
        """安排清理任务（简单实现，实际项目中可以使用任务队列）"""
        # 这里简单实现，直接删除
        # 实际项目中应该使用任务队列或定时任务
        try:
            if os.path.exists(upload_path):
                shutil.rmtree(upload_path)
        except Exception:
            # 忽略清理错误
            pass
    
    def cleanup_expired_uploads(self, hours: int = 24):
        """清理过期的上传会话"""
        if not os.path.exists(self.upload_dir):
            return
        
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=hours)
        
        for upload_id in os.listdir(self.upload_dir):
            upload_path = os.path.join(self.upload_dir, upload_id)
            metadata_file = os.path.join(upload_path, "metadata.json")
            
            if not os.path.exists(metadata_file):
                continue
            
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                created_at = datetime.fromisoformat(metadata["created_at"])
                status = metadata.get("status", "uploading")
                
                # 清理过期的或已完成/失败的上传会话
                if (created_at < cutoff_time or 
                    status in ["completed", "failed", "cancelled"]):
                    shutil.rmtree(upload_path)
                    
            except Exception:
                # 如果元数据文件损坏，直接删除
                try:
                    shutil.rmtree(upload_path)
                except Exception:
                    pass