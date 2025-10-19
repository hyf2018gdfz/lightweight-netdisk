# 个人网盘系统部署指南

基于 FastAPI 的轻量级个人云存储系统完整部署指南。

## 📋 系统要求

### 最低配置
- **Python**: 3.8+ (推荐 3.11+)
- **内存**: 512MB+ (推荐 1GB+)
- **磁盘**: 根据存储需求，建议至少 5GB 可用空间
- **操作系统**: Linux/Windows/macOS

### 推荐配置
- **CPU**: 双核以上
- **内存**: 2GB+
- **网络**: 稳定的网络连接
- **域名**: 用于生产环境部署

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <你的仓库地址>
cd personal-netdisk
```

### 2. 安装 Python 依赖

```bash
# 安装所需依赖
pip install -r requirements.txt
```

依赖包说明：
- `fastapi==0.104.1` - Web 框架
- `uvicorn[standard]==0.24.0` - ASGI 服务器
- `python-multipart==0.0.6` - 文件上传支持
- `jinja2==3.1.2` - 模板引擎
- `python-jose[cryptography]==3.3.0` - JWT 处理
- `passlib[bcrypt]==1.7.4` - 密码加密
- `sqlalchemy==2.0.23` - ORM 框架
- `aiofiles==23.2.1` - 异步文件操作
- `pillow==10.1.0` - 图片处理
- `python-magic==0.4.27` - 文件类型检测
- `pathvalidate==3.2.0` - 路径验证

### 3. 配置环境变量（可选）

系统使用环境变量进行配置，如不设置将使用默认值：

```bash
# 创建环境变量文件
cat > .env << 'EOF'
# 应用配置
HOST=0.0.0.0
PORT=8000
DEBUG=false

# 安全配置（生产环境必须修改）
SECRET_KEY=your-super-secret-key-change-in-production-environment
CORS_ORIGINS=*
TRUSTED_HOSTS=*

# 文件存储配置
STORAGE_PATH=./storage
TRASH_PATH=./trash
MAX_FILE_SIZE=104857600

# 速率限制
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60

# 数据库配置
DATABASE_URL=sqlite:///./database.db

# 清理配置
AUTO_CLEANUP_ENABLED=true
TRASH_RETENTION_DAYS=14
CLEANUP_INTERVAL_HOURS=24
EOF
```

### 4. 启动应用

**开发环境**：
```bash
python main.py
```

**生产环境**：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. 访问系统

- 打开浏览器访问：`http://localhost:8000`
- 默认管理员账户：
  - **用户名**: `admin`
  - **密码**: `admin123`

## 🐳 Docker 部署

### 方式一：Docker Compose（推荐）

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  netdisk:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./storage:/app/storage
      - ./trash:/app/trash
      - ./database.db:/app/database.db
    environment:
      - SECRET_KEY=your-super-secret-key-change-in-production
      - DEBUG=false
      - MAX_FILE_SIZE=104857600
      - CORS_ORIGINS=*
      - TRUSTED_HOSTS=*
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 可选：添加反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./static:/app/static:ro
    depends_on:
      - netdisk
    restart: unless-stopped
```

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p storage trash static templates

# 设置权限
RUN chmod +x main.py

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

启动服务：

```bash
docker-compose up -d
```

### 方式二：纯 Docker 部署

```bash
# 构建镜像
docker build -t personal-netdisk .

# 运行容器
docker run -d \
  --name netdisk \
  -p 8000:8000 \
  -v $(pwd)/storage:/app/storage \
  -v $(pwd)/trash:/app/trash \
  -v $(pwd)/database.db:/app/database.db \
  -e SECRET_KEY=your-super-secret-key \
  --restart unless-stopped \
  personal-netdisk
```

## 🔧 生产环境部署

### 方式一：使用 Gunicorn + Nginx

#### 1. 安装 Gunicorn

```bash
pip install gunicorn
```

#### 2. 创建 Gunicorn 配置

创建 `gunicorn.conf.py`：

```python
# Gunicorn 配置文件
import multiprocessing
import os

# 服务器配置
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# 性能配置
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True

# 日志配置
accesslog = "/var/log/netdisk/access.log"
errorlog = "/var/log/netdisk/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程配置
user = "netdisk"
group = "netdisk"
tmp_upload_dir = None
```

#### 3. 创建系统用户

```bash
# 创建系统用户
sudo useradd -r -s /bin/false netdisk

# 创建应用目录
sudo mkdir -p /opt/netdisk
sudo mkdir -p /var/log/netdisk

# 复制应用文件
sudo cp -r . /opt/netdisk/
sudo chown -R netdisk:netdisk /opt/netdisk
sudo chown -R netdisk:netdisk /var/log/netdisk
```

#### 4. 创建 Systemd 服务

创建 `/etc/systemd/system/netdisk.service`：

```ini
[Unit]
Description=Personal Netdisk Service
After=network.target
Wants=network.target

[Service]
Type=notify
User=netdisk
Group=netdisk
WorkingDirectory=/opt/netdisk
ExecStart=/opt/netdisk/venv/bin/gunicorn -c gunicorn.conf.py main:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5

# 环境变量
Environment=SECRET_KEY=your-super-secret-key-change-this
Environment=DEBUG=false
Environment=CORS_ORIGINS=https://yourdomain.com
Environment=TRUSTED_HOSTS=yourdomain.com

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable netdisk
sudo systemctl start netdisk
sudo systemctl status netdisk
```

#### 5. 配置 Nginx

创建 `/etc/nginx/sites-available/netdisk`：

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # 文件上传大小限制
    client_max_body_size 100M;
    
    # 主应用代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件直接服务
    location /static {
        alias /opt/netdisk/static;
        expires 30d;
        add_header Cache-Control "public, no-transform";
        
        # Gzip 压缩
        gzip on;
        gzip_types text/css application/javascript image/svg+xml;
    }
    
    # 安全头部
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy strict-origin-when-cross-origin;
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/netdisk /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 方式二：使用 Supervisor

安装 Supervisor：

```bash
sudo apt-get install supervisor
```

创建配置文件 `/etc/supervisor/conf.d/netdisk.conf`：

```ini
[program:netdisk]
command=/opt/netdisk/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
directory=/opt/netdisk
user=netdisk
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/netdisk/supervisor.log
environment=SECRET_KEY="your-super-secret-key",DEBUG="false"
```

启动：

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start netdisk
```

## 🔒 安全配置

### 1. SSL/HTTPS 配置

使用 Let's Encrypt 获取免费 SSL 证书：

```bash
# 安装 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自动续期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. 防火墙配置

```bash
# UFW 防火墙配置
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. 生产环境安全检查

确保修改以下配置：

```bash
# 必须修改的配置项
SECRET_KEY=复杂的随机字符串  # 至少32位
CORS_ORIGINS=https://yourdomain.com  # 具体域名
TRUSTED_HOSTS=yourdomain.com  # 具体域名
DEBUG=false  # 禁用调试模式
```

### 4. 文件权限设置

```bash
# 设置正确的文件权限
sudo chmod 755 /opt/netdisk
sudo chmod 644 /opt/netdisk/*.py
sudo chmod 700 /opt/netdisk/storage
sudo chmod 700 /opt/netdisk/trash
sudo chmod 600 /opt/netdisk/database.db
```

## 📊 监控和维护

### 健康检查

系统提供健康检查端点：

```bash
curl http://localhost:8000/health
# 响应：{"status": "ok", "message": "个人网盘系统运行正常"}
```

### 日志管理

日志位置：
- **应用日志**: `/var/log/netdisk/`
- **Nginx 日志**: `/var/log/nginx/`
- **系统日志**: `journalctl -u netdisk`

### 备份策略

```bash
#!/bin/bash
# 备份脚本示例
BACKUP_DIR="/backup/netdisk/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份数据库
cp /opt/netdisk/database.db $BACKUP_DIR/

# 备份文件存储
tar -czf $BACKUP_DIR/storage.tar.gz -C /opt/netdisk storage/

# 清理30天前的备份
find /backup/netdisk -name "20*" -type d -mtime +30 -exec rm -rf {} \;
```

### 系统维护

```bash
# 查看系统状态
sudo systemctl status netdisk

# 重启服务
sudo systemctl restart netdisk

# 查看日志
sudo journalctl -u netdisk -f

# 检查磁盘使用
df -h /opt/netdisk/storage

# 清理回收站（手动）
find /opt/netdisk/trash -type f -mtime +14 -delete
```

## 🎯 性能优化

### 1. 数据库优化

对于大量文件，建议使用 PostgreSQL 或 MySQL：

```bash
# PostgreSQL 配置示例
DATABASE_URL=postgresql://netdisk:password@localhost/netdisk
```

### 2. 缓存配置

可以在 Nginx 中添加缓存配置：

```nginx
# 在 Nginx 配置中添加
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=netdisk_cache:10m max_size=100m;

location /files/preview/ {
    proxy_cache netdisk_cache;
    proxy_cache_valid 200 10m;
    proxy_pass http://127.0.0.1:8000;
}
```

### 3. 文件存储优化

大文件存储建议：
- 使用对象存储（S3、MinIO 等）
- 启用文件压缩
- 实施文件去重

## 🔧 故障排除

### 常见问题

1. **无法启动服务**
```bash
# 检查端口占用
sudo netstat -tlnp | grep :8000

# 检查权限
ls -la /opt/netdisk/

# 查看详细错误
sudo journalctl -u netdisk -n 50
```

2. **文件上传失败**
```bash
# 检查磁盘空间
df -h

# 检查文件权限
ls -la storage/

# 检查日志
tail -f /var/log/netdisk/error.log
```

3. **无法访问网站**
```bash
# 检查 Nginx 状态
sudo systemctl status nginx

# 测试配置
sudo nginx -t

# 检查防火墙
sudo ufw status
```

### 调试模式

在开发环境中启用调试：

```bash
DEBUG=true python main.py
```

### 联系支持

遇到问题时，请提供：
- 系统版本信息
- 错误日志内容
- 配置文件内容（删除敏感信息）
- 问题复现步骤

---

**注意**：本文档基于项目实际代码结构编写，确保了配置的准确性和可执行性。在生产环境部署前，请务必修改默认密码和密钥。