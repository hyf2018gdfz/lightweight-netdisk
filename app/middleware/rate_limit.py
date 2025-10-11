"""
速率限制中间件
防止API滥用和暴力攻击
"""

import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # 允许的请求数
        self.period = period  # 时间窗口（秒）
        self.clients: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, time.time()))
    
    def get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用X-Forwarded-For头部
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # 使用客户端IP
        client_ip = request.client.host if request.client else "unknown"
        return client_ip
    
    def is_rate_limited(self, client_id: str) -> bool:
        """检查是否触发速率限制"""
        current_time = time.time()
        call_count, last_reset = self.clients[client_id]
        
        # 检查是否需要重置计数器
        if current_time - last_reset >= self.period:
            self.clients[client_id] = (1, current_time)
            return False
        
        # 检查是否超过限制
        if call_count >= self.calls:
            return True
        
        # 增加计数
        self.clients[client_id] = (call_count + 1, last_reset)
        return False
    
    def cleanup_expired(self):
        """清理过期的客户端记录"""
        current_time = time.time()
        expired_clients = []
        
        for client_id, (_, last_reset) in self.clients.items():
            if current_time - last_reset >= self.period * 2:  # 保留2个周期的数据
                expired_clients.append(client_id)
        
        for client_id in expired_clients:
            del self.clients[client_id]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端ID
        client_id = self.get_client_id(request)
        
        # 排除某些不需要限制的路径
        excluded_paths = ["/health", "/static"]
        if any(request.url.path.startswith(path) for path in excluded_paths):
            return await call_next(request)
        
        # 检查速率限制
        if self.is_rate_limited(client_id):
            # 返回429状态码
            return Response(
                content='{"detail": "请求过于频繁，请稍后再试"}',
                status_code=429,
                headers={
                    "Content-Type": "application/json",
                    "Retry-After": str(self.period),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + self.period))
                }
            )
        
        # 执行请求
        response = await call_next(request)
        
        # 添加速率限制信息到响应头
        client_calls, _ = self.clients[client_id]
        remaining = max(0, self.calls - client_calls)
        
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.period))
        
        # 定期清理过期记录
        if len(self.clients) > 1000:  # 当记录数超过1000时清理
            self.cleanup_expired()
        
        return response