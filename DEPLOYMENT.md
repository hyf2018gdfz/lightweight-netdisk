# 个人网盘系统部署指南

## 系统要求

- Python 3.8+
- 操作系统：Linux/Windows/macOS
- 内存：至少512MB
- 磁盘空间：根据存储需求而定

## 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd personal-netdisk
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，修改必要的配置：

```bash
# 必须修改的配置
SECRET_KEY=your-super-secret-key-here-change-in-production
CORS_ORIGINS=https://yourdomain.com
TRUSTED_HOSTS=yourdomain.com

# 可选配置
MAX_FILE_SIZE=104857600  # 100MB
RATE_LIMIT_CALLS=100
```

### 4. 初始化数据库

```bash
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 5. 运行应用

开发环境：
```bash
python main.py
```

生产环境：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 生产环境部署

### 使用 Gunicorn + Nginx

#### 1. 安装 Gunicorn

```bash
pip install gunicorn
```

#### 2. 创建 Gunicorn 配置文件

创建 `gunicorn.conf.py`：

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

#### 3. 启动 Gunicorn

```bash
gunicorn -c gunicorn.conf.py main:app
```

#### 4. 配置 Nginx

创建 Nginx 配置文件 `/etc/nginx/sites-available/netdisk`：

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /static {
        alias /path/to/your/app/static;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```

启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/netdisk /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 使用 Docker

#### 1. 创建 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p storage trash static templates

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. 创建 docker-compose.yml

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
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./static:/app/static
    depends_on:
      - netdisk
    restart: unless-stopped
```

#### 3. 构建和运行

```bash
docker-compose up -d
```

### 使用 Systemd 服务

创建服务文件 `/etc/systemd/system/netdisk.service`：

```ini
[Unit]
Description=Personal Netdisk Service
After=network.target

[Service]
Type=exec
User=netdisk
Group=netdisk
WorkingDirectory=/opt/netdisk
ExecStart=/opt/netdisk/venv/bin/gunicorn -c gunicorn.conf.py main:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用和启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable netdisk
sudo systemctl start netdisk
```

## 安全配置

### 1. HTTPS 配置

使用 Let's Encrypt 获取 SSL 证书：

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 2. 防火墙配置

```bash
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. 安全头部

系统已自动配置以下安全头部：
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Content-Security-Policy
- Referrer-Policy

### 4. 速率限制

默认配置为每分钟100次请求，可通过环境变量调整：
```bash
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60
```

## 备份和恢复

### 数据备份

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/netdisk"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp database.db $BACKUP_DIR/database_$DATE.db

# 备份存储文件
tar -czf $BACKUP_DIR/storage_$DATE.tar.gz storage/

# 备份配置文件
cp .env $BACKUP_DIR/env_$DATE

echo "备份完成: $BACKUP_DIR"
```

### 数据恢复

```bash
#!/bin/bash
# restore.sh
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: ./restore.sh <backup_file>"
    exit 1
fi

# 停止服务
sudo systemctl stop netdisk

# 恢复数据库
cp $BACKUP_FILE/database_*.db database.db

# 恢复存储文件
tar -xzf $BACKUP_FILE/storage_*.tar.gz

# 启动服务
sudo systemctl start netdisk

echo "恢复完成"
```

## 监控和日志

### 日志配置

应用日志级别可通过环境变量设置：
```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### 系统监控

可以使用以下工具监控应用：
- Prometheus + Grafana
- 自带的健康检查端点：`/health`

### 日志轮转

配置 logrotate：

```bash
# /etc/logrotate.d/netdisk
/var/log/netdisk/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 netdisk netdisk
    postrotate
        systemctl reload netdisk
    endscript
}
```

## 故障排除

### 常见问题

1. **文件上传失败**
   - 检查文件大小限制：`MAX_FILE_SIZE`
   - 检查磁盘空间
   - 检查文件权限

2. **数据库错误**
   - 检查数据库文件权限
   - 确保数据库文件存在

3. **静态文件无法访问**
   - 检查静态文件目录权限
   - 确保 Nginx 配置正确

4. **速率限制过于严格**
   - 调整 `RATE_LIMIT_CALLS` 和 `RATE_LIMIT_PERIOD`

### 性能优化

1. **数据库优化**
   - 使用 PostgreSQL 或 MySQL 替代 SQLite
   - 定期执行 VACUUM（SQLite）

2. **文件存储优化**
   - 使用 SSD 存储
   - 配置适当的文件系统

3. **缓存优化**
   - 配置 Nginx 静态文件缓存
   - 使用 Redis 缓存（可选）

## 维护

### 定期维护任务

1. **清理过期文件**：系统会自动清理，也可手动执行
2. **备份数据**：建议每日备份
3. **更新依赖**：定期更新 Python 包
4. **监控日志**：检查错误日志

### 升级指南

1. 备份当前数据
2. 拉取新版本代码
3. 更新依赖：`pip install -r requirements.txt`
4. 重启应用

## 技术支持

- 系统状态检查：访问 `/health`
- 查看日志文件
- 检查系统资源使用情况
- 运行测试脚本：`python test_system.py`