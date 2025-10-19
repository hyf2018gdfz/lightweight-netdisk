"""
文件处理工具函数
"""

import os
import zipfile
import tempfile
from typing import List, BinaryIO
from pathlib import Path
from app.models.file import FileNode
from app.config import STORAGE_DIR, PREVIEW_EXTENSIONS


def is_image(node: FileNode) -> bool:
    """判断是否为图片文件"""
    if not node.is_file:
        return False
    return node.file_extension in PREVIEW_EXTENSIONS.get('image', set())


def is_text(node: FileNode) -> bool:
    """判断是否为文本文件"""
    if not node.is_file:
        return False
    return node.file_extension in PREVIEW_EXTENSIONS.get('text', set())


def is_pdf(node: FileNode) -> bool:
    """判断是否为PDF文件"""
    if not node.is_file:
        return False
    return node.file_extension in PREVIEW_EXTENSIONS.get('pdf', set())


def is_audio(node: FileNode) -> bool:
    """判断是否为音频文件"""
    if not node.is_file:
        return False
    return node.file_extension in PREVIEW_EXTENSIONS.get('audio', set())


def is_video(node: FileNode) -> bool:
    """判断是否为视频文件"""
    if not node.is_file:
        return False
    return node.file_extension in PREVIEW_EXTENSIONS.get('video', set())


def can_preview(node: FileNode) -> bool:
    """判断文件是否可以预览"""
    return is_image(node) or is_text(node) or is_pdf(node) or is_audio(node) or is_video(node)


def get_file_content(node: FileNode) -> bytes:
    """读取文件内容"""
    if not node.is_file or node.is_deleted:
        raise ValueError("无效的文件节点")
    
    file_path = node.physical_path
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    with open(file_path, 'rb') as f:
        return f.read()


def get_text_content(node: FileNode, encoding: str = 'utf-8') -> str:
    """读取文本文件内容"""
    if not is_text(node):
        raise ValueError("不是文本文件")
    
    content = get_file_content(node)
    
    # 尝试不同的编码
    encodings = [encoding, 'utf-8', 'gbk', 'gb2312', 'latin-1']
    
    for enc in encodings:
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    
    # 如果所有编码都失败，使用错误处理
    return content.decode('utf-8', errors='replace')


def create_zip_from_nodes(nodes: List[FileNode], base_path: str = "") -> bytes:
    """从文件节点列表创建ZIP文件"""
    if not nodes:
        raise ValueError("没有要打包的文件")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile() as temp_file:
        with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for node in nodes:
                _add_node_to_zip(zipf, node, base_path)
        
        # 读取ZIP文件内容
        temp_file.seek(0)
        return temp_file.read()


def _add_node_to_zip(zipf: zipfile.ZipFile, node: FileNode, base_path: str = ""):
    """递归添加节点到ZIP文件"""
    if node.is_deleted:
        return
    
    # 计算在ZIP中的路径
    zip_path = os.path.join(base_path, node.name) if base_path else node.name
    
    if node.is_file:
        # 添加文件
        file_path = node.physical_path
        if os.path.exists(file_path):
            zipf.write(file_path, zip_path)
    
    elif node.is_directory:
        # 添加目录（如果为空目录，创建一个空目录项）
        children = node.get_children()
        if not children:
            # 空目录
            zipf.writestr(zip_path + '/', '')
        else:
            # 递归添加子节点
            for child in children:
                _add_node_to_zip(zipf, child, zip_path)


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    i = 0
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    if i == 0:
        return f"{int(size)} {size_names[i]}"
    else:
        return f"{size:.1f} {size_names[i]}"


def get_file_icon(node: FileNode) -> str:
    """获取文件图标"""
    if node.is_directory:
        return "📁"
    
    if not node.file_extension:
        return "📄"
    
    # 根据文件扩展名返回相应图标
    icon_map = {
        # 图片
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', 
        '.bmp': '🖼️', '.webp': '🖼️', '.svg': '🖼️',
        
        # 文档
        '.txt': '📝', '.md': '📝', '.doc': '📄', '.docx': '📄',
        '.pdf': '📋', '.rtf': '📄',
        
        # 代码
        '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨',
        '.json': '⚙️', '.xml': '⚙️', '.sql': '🗄️',
        
        # 压缩
        '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦', '.gz': '📦',
        
        # 音频
        '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵', '.aac': '🎵',
        
        # 视频
        '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬', '.mov': '🎬', '.wmv': '🎬',
        
        # 其他
        '.exe': '⚙️', '.app': '⚙️', '.deb': '📦', '.rpm': '📦',
    }
    
    return icon_map.get(node.file_extension, '📄')


def is_safe_path(path: str) -> bool:
    """检查路径是否安全（防止路径遍历攻击）"""
    # 标准化路径
    normalized = os.path.normpath(path)
    
    # 检查是否包含相对路径组件
    if '..' in normalized.split(os.sep):
        return False
    
    # 检查是否为绝对路径
    if os.path.isabs(normalized):
        return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除危险字符"""
    # 移除或替换危险字符
    dangerous_chars = '<>:"/\\|?*'
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # 移除开头和结尾的空格和点
    filename = filename.strip(' .')
    
    # 确保文件名不为空
    if not filename:
        filename = 'unnamed'
    
    # 限制文件名长度
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        max_name_len = 255 - len(ext)
        filename = name[:max_name_len] + ext
    
    return filename


def calculate_directory_size(node: FileNode) -> int:
    """计算目录大小（递归）"""
    if not node.is_directory:
        return node.file_size or 0
    
    total_size = 0
    for child in node.get_all_descendants():
        if child.is_file and not child.is_deleted:
            total_size += child.file_size or 0
    
    return total_size