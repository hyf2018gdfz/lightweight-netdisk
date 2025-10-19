# API 文档

个人网盘系统 REST API 完整文档。

## 📖 概述

本系统基于 FastAPI 构建，提供完整的 RESTful API 接口。所有 API 均支持 JSON 格式的请求和响应。

### 基础信息
- **基础URL**: `http://localhost:8000`
- **API版本**: v1.0.0
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

### 快速链接
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI 规范**: http://localhost:8000/openapi.json

## 🔐 认证系统

### 认证流程

1. **登录获取 Token**
2. **在请求头中携带 Token**
3. **Token 过期后重新登录**

### Token 格式
```http
Authorization: Bearer <your-jwt-token>
```

### 认证 API

#### POST /auth/login
用户登录

**请求体**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "is_active": true
  }
}
```

#### GET /auth/me
获取当前用户信息

**响应示例**:
```json
{
  "id": 1,
  "username": "admin",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00"
}
```

#### POST /auth/logout
用户登出

**响应示例**:
```json
{
  "message": "登出成功"
}
```

#### PUT /auth/change-password
修改密码

**请求体**:
```json
{
  "old_password": "admin123",
  "new_password": "new_password"
}
```

#### GET /auth/check
检查登录状态

## 📁 文件管理 API

### 文件操作

#### GET /files/browse
浏览目录

**参数**:
- `path` (string, optional): 目录路径，默认为 "/"

**响应示例**:
```json
{
  "path": "/",
  "parent_path": null,
  "items": [
    {
      "id": 1,
      "name": "文档",
      "full_path": "/文档",
      "is_file": false,
      "is_directory": true,
      "file_size": 0,
      "created_at": "2024-01-01T00:00:00",
      "icon": "fas fa-folder",
      "can_preview": false
    },
    {
      "id": 2,
      "name": "test.txt",
      "full_path": "/test.txt",
      "is_file": true,
      "is_directory": false,
      "file_size": 1024,
      "formatted_size": "1.0 KB",
      "mime_type": "text/plain",
      "created_at": "2024-01-01T00:00:00",
      "icon": "fas fa-file-text",
      "can_preview": true
    }
  ]
}
```

#### POST /files/upload
上传文件

**请求格式**: `multipart/form-data`

**参数**:
- `files` (file[]): 要上传的文件列表
- `path` (string, optional): 上传目录路径，默认为 "/"
- `relative_paths` (string, optional): 文件相对路径的 JSON 字符串，用于文件夹上传

**响应示例**:
```json
{
  "success": true,
  "message": "成功上传 2 个文件",
  "file_info": {
    "uploaded": [
      {
        "id": 3,
        "name": "document.pdf",
        "full_path": "/document.pdf",
        "file_size": 2048576,
        "formatted_size": "2.0 MB"
      }
    ],
    "errors": []
  }
}
```

#### POST /files/mkdir
创建目录

**请求体**:
```json
{
  "path": "/新建文件夹"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "目录 '新建文件夹' 创建成功",
  "file_info": {
    "id": 4,
    "name": "新建文件夹",
    "full_path": "/新建文件夹",
    "is_directory": true
  }
}
```

#### GET /files/download/{node_id}
下载文件

**支持特性**:
- 单文件下载
- 目录打包下载（ZIP 格式）
- 断点续传（HTTP Range 请求）

**参数**:
- `node_id` (integer): 文件或目录的 ID

**HTTP 头部**:
- `Range` (optional): 指定下载范围，格式如 "bytes=0-1023"

**响应**:
- 单文件：二进制文件流
- 目录：ZIP 压缩包

#### PUT /files/rename/{node_id}
重命名文件或目录

**请求体**:
```json
{
  "new_name": "新文件名.txt"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "'旧文件名.txt' 重命名为 '新文件名.txt' 成功"
}
```

#### DELETE /files/delete/{node_id}
删除文件或目录（移入回收站）

**响应示例**:
```json
{
  "success": true,
  "message": "'文件名.txt' 已移入回收站"
}
```

#### GET /files/preview/{node_id}
预览文件

**支持的文件类型**:
- 文本文件：.txt, .md, .json, .xml, .html, .css, .js, .py
- 图片文件：.jpg, .jpeg, .png, .gif, .bmp, .webp
- PDF 文件：.pdf
- 音频文件：.mp3, .wav, .flac, .aac, .ogg, .m4a
- 视频文件：.mp4, .avi, .mkv, .mov, .wmv, .webm, .m4v

**文本文件响应示例**:
```json
{
  "type": "text",
  "content": "文件内容...",
  "filename": "test.txt",
  "size": 1024
}
```

**图片/PDF/音视频文件**: 直接返回文件内容

#### GET /files/search
搜索文件

**参数**:
- `keyword` (string, required): 搜索关键词
- `path` (string, optional): 搜索路径，默认为 "/"

**响应示例**:
```json
{
  "keyword": "test",
  "results": [
    {
      "id": 2,
      "name": "test.txt",
      "full_path": "/documents/test.txt",
      "is_file": true,
      "file_size": 1024,
      "formatted_size": "1.0 KB"
    }
  ],
  "total": 1
}
```

## 🗑️ 回收站 API

#### GET /trash/list
获取回收站列表

**响应格式**: 与 `/files/browse` 相同

#### POST /trash/restore/{node_id}
恢复文件

**响应示例**:
```json
{
  "success": true,
  "message": "'文件名.txt' 已恢复到原位置"
}
```

#### DELETE /trash/permanent/{node_id}
永久删除文件

**响应示例**:
```json
{
  "success": true,
  "message": "'文件名.txt' 已永久删除"
}
```

#### POST /trash/empty
清空回收站

**响应示例**:
```json
{
  "success": true,
  "message": "回收站已清空，删除了 5 个项目"
}
```

#### POST /trash/auto-clean
执行自动清理

**响应示例**:
```json
{
  "success": true,
  "message": "自动清理完成，删除了 3 个过期项目"
}
```

## 📤 分享系统 API

### 分享管理

#### POST /share/create
创建分享

**请求体**:
```json
{
  "node_id": 1,
  "description": "分享描述",
  "password": "123456",
  "expire_hours": 168,
  "download_limit": 10
}
```

**响应示例**:
```json
{
  "share_id": "abc123def456",
  "share_url": "http://localhost:8000/share/abc123def456",
  "password": "123456",
  "expire_time": "2024-01-08T00:00:00",
  "download_limit": 10,
  "file_info": {
    "name": "共享文件.txt",
    "size": 1024
  }
}
```

#### GET /share/list
获取我的分享列表

**响应示例**:
```json
{
  "shares": [
    {
      "share_id": "abc123def456",
      "file_name": "共享文件.txt",
      "description": "分享描述",
      "created_at": "2024-01-01T00:00:00",
      "expire_time": "2024-01-08T00:00:00",
      "download_count": 5,
      "download_limit": 10,
      "has_password": true,
      "is_expired": false
    }
  ]
}
```

### 分享访问

#### GET /share/{share_id}
访问分享页面

**返回**: HTML 页面

#### POST /share/{share_id}/access
验证分享密码

**请求体**:
```json
{
  "password": "123456"
}
```

**响应示例**:
```json
{
  "success": true,
  "file_info": {
    "name": "共享文件.txt",
    "size": 1024,
    "can_preview": true
  }
}
```

#### GET /share/{share_id}/download
下载分享的文件

**响应**: 文件内容

#### GET /share/{share_id}/preview
预览分享的文件

**响应格式**: 与 `/files/preview/{node_id}` 相同

### 分享编辑

#### PUT /share/{share_id}
更新分享

**请求体**:
```json
{
  "description": "新的分享描述",
  "password": "new_password",
  "expire_hours": 72,
  "download_limit": 20
}
```

#### DELETE /share/{share_id}
删除分享

**响应示例**:
```json
{
  "success": true,
  "message": "分享已删除"
}
```

#### GET /share/{share_id}/info
获取分享信息

**响应示例**:
```json
{
  "share_id": "abc123def456",
  "file_name": "共享文件.txt",
  "file_size": 1024,
  "description": "分享描述",
  "created_at": "2024-01-01T00:00:00",
  "expire_time": "2024-01-08T00:00:00",
  "download_count": 5,
  "download_limit": 10,
  "has_password": true,
  "is_expired": false
}
```

## 🌐 页面路由

### 主要页面

#### GET /
主页面 - 文件管理界面

#### GET /trash
回收站页面

#### GET /shares  
分享管理页面

#### GET /{path:path}
动态文件夹路径页面（如：/documents、/images 等）

#### GET /health
健康检查端点

**响应示例**:
```json
{
  "status": "ok",
  "message": "个人网盘系统运行正常"
}
```

## 📋 数据模型

### FileNodeResponse
文件节点响应模型

```json
{
  "id": 1,
  "name": "文件名.txt",
  "full_path": "/path/to/文件名.txt",
  "is_file": true,
  "is_directory": false,
  "file_size": 1024,
  "formatted_size": "1.0 KB",
  "mime_type": "text/plain",
  "file_extension": ".txt",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "icon": "fas fa-file-text",
  "can_preview": true
}
```

### DirectoryListResponse
目录列表响应模型

```json
{
  "path": "/current/path",
  "parent_path": "/parent/path",
  "items": [FileNodeResponse, ...]
}
```

### SearchResponse
搜索结果响应模型

```json
{
  "keyword": "search_term",
  "results": [FileNodeResponse, ...],
  "total": 10
}
```

### ShareResponse
分享创建响应模型

```json
{
  "share_id": "unique_share_id",
  "share_url": "http://localhost:8000/share/unique_share_id",
  "password": "share_password",
  "expire_time": "2024-01-08T00:00:00Z",
  "download_limit": 10,
  "file_info": {
    "name": "shared_file.txt",
    "size": 1024
  }
}
```

## ⚠️ 错误处理

### HTTP 状态码
- **200 OK**: 请求成功
- **201 Created**: 资源创建成功
- **206 Partial Content**: 部分内容响应（断点续传）
- **400 Bad Request**: 请求参数错误
- **401 Unauthorized**: 未认证或认证失败
- **403 Forbidden**: 权限不足
- **404 Not Found**: 资源不存在
- **413 Payload Too Large**: 文件过大
- **416 Range Not Satisfiable**: 范围请求无效
- **422 Unprocessable Entity**: 请求参数验证失败
- **429 Too Many Requests**: 请求频率过高
- **500 Internal Server Error**: 服务器内部错误

### 错误响应格式

```json
{
  "detail": "错误详细信息"
}
```

### 验证错误响应格式

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 🔒 安全说明

### 认证安全
- JWT Token 有效期为 7 天
- 密码使用 bcrypt 加密存储
- 支持密码修改功能

### 文件安全
- 文件路径验证，防止目录遍历攻击
- 文件大小限制（默认 100MB）
- 文件类型检测和验证
- 用户文件隔离存储

### API 安全
- 速率限制：每分钟 100 次请求
- CORS 配置可控
- 安全头部自动添加
- 输入参数严格验证

### 分享安全
- 分享链接使用随机 ID
- 支持密码保护
- 可设置过期时间
- 可限制下载次数

## 📊 性能特性

### 文件处理
- **断点续传**: 支持 HTTP Range 请求
- **流式传输**: 大文件不占用内存
- **压缩打包**: 目录下载自动压缩为 ZIP
- **异步处理**: 所有文件操作异步进行

### 数据库优化
- **索引优化**: 关键字段建立索引
- **查询优化**: 避免 N+1 查询问题
- **连接池**: 数据库连接复用

### 缓存策略
- **静态文件缓存**: 30 天浏览器缓存
- **API 响应**: 可配置缓存头部
- **文件预览**: 支持条件请求

## 🧪 测试 API

### 使用 curl 测试

```bash
# 1. 登录获取 token
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  jq -r '.access_token')

# 2. 浏览根目录
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/files/browse?path=/"

# 3. 上传文件
curl -H "Authorization: Bearer $TOKEN" \
  -F "files=@test.txt" \
  -F "path=/" \
  "http://localhost:8000/files/upload"

# 4. 搜索文件
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/files/search?keyword=test"

# 5. 创建分享
curl -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"node_id":1,"description":"测试分享","expire_hours":24}' \
  "http://localhost:8000/share/create"
```

### 使用 Python 测试

```python
import requests

# 基础配置
BASE_URL = "http://localhost:8000"
session = requests.Session()

# 登录
login_response = session.post(f"{BASE_URL}/auth/login", json={
    "username": "admin", 
    "password": "admin123"
})
token = login_response.json()["access_token"]
session.headers.update({"Authorization": f"Bearer {token}"})

# 浏览目录
files = session.get(f"{BASE_URL}/files/browse").json()
print(f"找到 {len(files['items'])} 个项目")

# 上传文件
with open("test.txt", "rb") as f:
    upload_response = session.post(f"{BASE_URL}/files/upload", 
        files={"files": f}, 
        data={"path": "/"}
    )
print(upload_response.json())
```

## 📚 扩展开发

### 添加新的 API 端点

1. **定义数据模型** (schemas)
2. **实现路由处理** (routers)
3. **添加业务逻辑** (services)
4. **编写测试用例**
5. **更新文档**

### 集成第三方存储

可以扩展 `FileService` 类来支持：
- Amazon S3
- 阿里云 OSS
- 腾讯云 COS
- MinIO

### 添加新的预览类型

在 `file_utils.py` 中添加：
- 新的文件类型检测函数
- 预览处理逻辑
- 对应的图标和样式

---

**注意**: 本文档基于实际代码自动生成，确保 API 描述的准确性。如有疑问，请参考自动生成的 Swagger UI 文档。