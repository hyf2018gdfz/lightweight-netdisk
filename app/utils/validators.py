"""
输入验证工具
提供各种输入验证功能
"""

import re
import os
from typing import Optional
from pathvalidate import is_valid_filename, sanitize_filename


def validate_filename(filename: str) -> bool:
    """
    验证文件名是否合法
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否合法
    """
    if not filename or not filename.strip():
        return False
    
    # 长度限制
    if len(filename) > 255:
        return False
    
    # 使用pathvalidate库验证
    return is_valid_filename(filename)


def sanitize_file_name(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    if not filename:
        return "unnamed_file"
    
    # 使用pathvalidate库清理
    sanitized = sanitize_filename(filename)
    
    # 如果清理后为空，使用默认名称
    if not sanitized.strip():
        return "unnamed_file"
    
    return sanitized


def validate_path(path: str) -> bool:
    """
    验证路径是否安全（防止路径遍历攻击）
    
    Args:
        path: 文件路径
        
    Returns:
        bool: 是否安全
    """
    if not path:
        return False
    
    # 规范化路径
    normalized_path = os.path.normpath(path)
    
    # 检查是否包含危险字符
    dangerous_patterns = [
        "..",  # 父级目录
        "~",   # 用户主目录
        "//",  # 双斜杠
    ]
    
    for pattern in dangerous_patterns:
        if pattern in normalized_path:
            return False
    
    # 检查是否为绝对路径（应该为相对路径）
    if os.path.isabs(normalized_path):
        return False
    
    return True


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    验证密码强度
    
    Args:
        password: 密码
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    if not password:
        return False, "密码不能为空"
    
    if len(password) < 6:
        return False, "密码长度至少6位"
    
    if len(password) > 50:
        return False, "密码长度不能超过50位"
    
    # 检查是否包含至少一个字母和一个数字
    has_letter = re.search(r'[a-zA-Z]', password) is not None
    has_digit = re.search(r'\d', password) is not None
    
    if not (has_letter and has_digit):
        return False, "密码必须包含至少一个字母和一个数字"
    
    return True, None


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    验证用户名格式
    
    Args:
        username: 用户名
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    if not username:
        return False, "用户名不能为空"
    
    if len(username) < 3:
        return False, "用户名长度至少3位"
    
    if len(username) > 20:
        return False, "用户名长度不能超过20位"
    
    # 只允许字母、数字、下划线
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"
    
    return True, None


def validate_share_description(description: Optional[str]) -> bool:
    """
    验证分享描述
    
    Args:
        description: 分享描述
        
    Returns:
        bool: 是否有效
    """
    if description is None:
        return True
    
    if len(description) > 200:
        return False
    
    return True


def validate_file_size(file_size: int, max_size: int = 100 * 1024 * 1024) -> tuple[bool, Optional[str]]:
    """
    验证文件大小
    
    Args:
        file_size: 文件大小（字节）
        max_size: 最大允许大小（默认100MB）
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    if file_size <= 0:
        return False, "文件大小必须大于0"
    
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        return False, f"文件大小不能超过{max_size_mb:.1f}MB"
    
    return True, None


def validate_mime_type(mime_type: str, allowed_types: Optional[list] = None) -> bool:
    """
    验证MIME类型
    
    Args:
        mime_type: MIME类型
        allowed_types: 允许的类型列表，None表示允许所有类型
        
    Returns:
        bool: 是否允许
    """
    if not mime_type:
        return False
    
    if allowed_types is None:
        return True
    
    # 检查是否在允许列表中
    for allowed_type in allowed_types:
        if mime_type.startswith(allowed_type):
            return True
    
    return False


def clean_search_keyword(keyword: str) -> str:
    """
    清理搜索关键词
    
    Args:
        keyword: 原始关键词
        
    Returns:
        str: 清理后的关键词
    """
    if not keyword:
        return ""
    
    # 移除前后空格
    keyword = keyword.strip()
    
    # 限制长度
    if len(keyword) > 100:
        keyword = keyword[:100]
    
    # 移除危险字符（防止SQL注入等）
    dangerous_chars = ["'", '"', ";", "\\", "/", "*", "?", "<", ">", "|"]
    for char in dangerous_chars:
        keyword = keyword.replace(char, "")
    
    return keyword