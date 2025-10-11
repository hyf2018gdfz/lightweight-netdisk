"""
文件清理工具
"""

import threading
import time
from datetime import datetime, timedelta
from app.database import get_db_context
from app.models.file import FileNode
from app.services.file_service import FileService
from app.config import TRASH_RETENTION_DAYS

# 全局变量控制清理线程
_cleaner_thread = None
_stop_cleaner = False


def cleanup_expired_files():
    """清理过期文件"""
    try:
        with get_db_context() as db:
            # 计算过期时间
            expire_date = datetime.utcnow() - timedelta(days=TRASH_RETENTION_DAYS)
            
            # 查询过期的已删除文件
            expired_files = db.query(FileNode).filter(
                FileNode.is_deleted == True,
                FileNode.deleted_at <= expire_date
            ).all()
            
            if not expired_files:
                print("🗑️ 没有过期文件需要清理")
                return 0
            
            file_service = FileService(db)
            success_count = 0
            
            for node in expired_files:
                try:
                    if file_service.permanent_delete(node):
                        success_count += 1
                        print(f"🗑️ 已清理过期文件: {node.full_path}")
                except Exception as e:
                    print(f"⚠️ 清理文件失败 {node.full_path}: {e}")
            
            print(f"✅ 自动清理完成，共清理 {success_count} 个过期文件")
            return success_count
            
    except Exception as e:
        print(f"❌ 清理任务失败: {e}")
        return 0


def file_cleaner_worker():
    """文件清理线程工作函数"""
    print("🗑️ 文件清理线程已启动")
    
    while not _stop_cleaner:
        try:
            # 每24小时执行一次清理
            cleanup_expired_files()
            
            # 等待 24 小时，每分钟检查一次停止信号
            for _ in range(24 * 60):  # 24小时 * 60分钟
                if _stop_cleaner:
                    break
                time.sleep(60)  # 等待 1 分钟
                
        except Exception as e:
            print(f"❌ 清理线程异常: {e}")
            # 异常后等待 1 小时再试
            for _ in range(60):
                if _stop_cleaner:
                    break
                time.sleep(60)
    
    print("🗑️ 文件清理线程已停止")


def start_file_cleaner():
    """启动文件清理任务"""
    global _cleaner_thread
    
    if _cleaner_thread is not None and _cleaner_thread.is_alive():
        print("⚠️ 文件清理任务已在运行")
        return
    
    # 创建并启动清理线程
    _cleaner_thread = threading.Thread(target=file_cleaner_worker, daemon=True)
    _cleaner_thread.start()
    
    print("✅ 文件清理任务已启动（每24小时执行一次）")


def stop_file_cleaner():
    """停止文件清理任务"""
    global _stop_cleaner, _cleaner_thread
    
    _stop_cleaner = True
    
    if _cleaner_thread and _cleaner_thread.is_alive():
        print("🗑️ 正在停止文件清理任务...")
        _cleaner_thread.join(timeout=5)  # 等待最多5秒
    
    _cleaner_thread = None
    print("✅ 文件清理任务已停止")


def manual_cleanup():
    """手动执行一次清理"""
    print("🗑️ 执行手动清理...")
    return cleanup_expired_files()