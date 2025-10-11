"""
安全头部中间件
添加各种安全相关的HTTP头部
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头部中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 安全头部
        security_headers = {
            # 防止点击劫持攻击
            "X-Frame-Options": "DENY",
            
            # 防止MIME类型嗅探
            "X-Content-Type-Options": "nosniff",
            
            # XSS保护
            "X-XSS-Protection": "1; mode=block",
            
            # 引用策略
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # 内容安全策略
            "Content-Security-Policy": (
                "default-src 'self'; "
                "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
                "script-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "font-src 'self' https://cdnjs.cloudflare.com; "
                "connect-src 'self'"
            ),
            
            # 严格传输安全（生产环境启用HTTPS时使用）
            # "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            
            # 权限策略
            "Permissions-Policy": (
                "camera=(), "
                "microphone=(), "
                "geolocation=(), "
                "payment=(), "
                "usb=()"
            ),
            
            # 服务器标识
            "Server": "Netdisk/1.0"
        }
        
        # 添加安全头部
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response