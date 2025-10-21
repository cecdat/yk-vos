# YK-VOS 项目部署指南

## 📋 前置要求

- Docker 和 Docker Compose
- Ubuntu 服务器（推荐 20.04+）
- 至少 2GB RAM
- 开放端口：3000（前端）、8000（后端 API）

## 🚀 快速开始

### 1. 克隆或上传项目

```bash
cd /path/to/your/projects
# 如果是上传的压缩包
unzip yk-vos.zip
cd yk-vos
```

### 2. 配置环境变量

#### 后端环境变量

创建 `backend/.env` 文件（或复制示例文件）：

```bash
# 自动从示例文件复制
cp backend/.env.example backend/.env
```

编辑 `backend/.env`：

```env
# 数据库配置
DATABASE_URL=postgresql://vos:vos123@db:5432/vosdb

# Redis 配置
REDIS_URL=redis://redis:6379/0

# JWT 密钥（生产环境务必修改！）
SECRET_KEY=your-very-secret-key-change-this-in-production

# API 配置
API_V1_PREFIX=/api/v1
PROJECT_NAME=YK-VOS API
```

#### 前端环境变量

创建 `frontend/.env` 文件：

```bash
cat > frontend/.env << 'EOF'
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
EOF
```

如果是在服务器上运行，修改为服务器 IP：

```env
NEXT_PUBLIC_API_BASE=http://YOUR_SERVER_IP:8000/api/v1
```

### 3. 启动所有服务

```bash
docker-compose up --build -d
```

查看日志：

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 4. 验证服务状态

```bash
# 检查容器状态
docker-compose ps

# 应该看到以下容器运行中：
# - yk_vos_backend
# - yk_vos_frontend
# - yk_vos_celery
# - yk_vos_celery_beat
# - yk_vos_postgres
# - yk_vos_redis
```

### 5. 访问应用

- **前端界面**: http://YOUR_SERVER_IP:3000
- **后端 API 文档**: http://YOUR_SERVER_IP:8000/docs
- **API 健康检查**: http://YOUR_SERVER_IP:8000/health

### 6. 登录系统

默认管理员账号：
- **用户名**: `admin`
- **密码**: `Ykxx@2025`

## 🔧 常用操作

### 重启服务

```bash
docker-compose restart
```

### 停止服务

```bash
docker-compose stop
```

### 停止并删除容器

```bash
docker-compose down
```

### 查看后端日志

```bash
docker-compose logs -f backend
```

### 查看 Celery 任务日志

```bash
docker-compose logs -f celery
docker-compose logs -f celery-beat
```

### 进入后端容器

```bash
docker exec -it yk_vos_backend /bin/sh
```

### 手动执行数据库迁移

```bash
docker exec -it yk_vos_backend alembic upgrade head
```

### 手动创建管理员账号

```bash
docker exec -it yk_vos_backend python /srv/app/scripts/init_admin.py
```

## 🗄️ 数据库管理

### 连接到 PostgreSQL

```bash
docker exec -it yk_vos_postgres psql -U vos -d vosdb
```

### 备份数据库

```bash
docker exec yk_vos_postgres pg_dump -U vos vosdb > backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
cat backup_20250101.sql | docker exec -i yk_vos_postgres psql -U vos -d vosdb
```

## 📊 Celery 定时任务

项目包含以下自动任务：

1. **同步在线话机** - 每 5 分钟执行一次
   - 任务：`app.tasks.sync_tasks.sync_all_instances_online_phones`
   
2. **同步 CDR 话单** - 每天凌晨 1:30 执行
   - 任务：`app.tasks.sync_tasks.sync_all_instances_cdrs`

### 手动触发任务

进入 Celery 容器：

```bash
docker exec -it yk_vos_celery /bin/sh
```

在容器内执行：

```python
# 启动 Python
python

# 导入任务
from app.tasks.sync_tasks import sync_all_instances_online_phones, sync_all_instances_cdrs

# 执行同步话机任务
sync_all_instances_online_phones.delay()

# 执行同步 CDR 任务
sync_all_instances_cdrs.delay()
```

## 🔍 故障排查

### 前端无法连接后端

1. 检查 `frontend/.env` 中的 API 地址是否正确
2. 确认后端容器正在运行：`docker-compose ps`
3. 检查后端日志：`docker-compose logs backend`

### 数据库连接失败

1. 检查 PostgreSQL 容器状态：`docker-compose ps db`
2. 检查数据库日志：`docker-compose logs db`
3. 验证 `backend/.env` 中的数据库连接字符串

### Celery 任务不执行

1. 检查 Redis 容器状态：`docker-compose ps redis`
2. 查看 Celery 日志：`docker-compose logs celery celery-beat`
3. 确认 Celery Beat 正在运行

### 端口冲突

如果端口 3000 或 8000 已被占用，修改 `docker-compose.yml`：

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # 改为其他端口
  
  frontend:
    ports:
      - "3001:3000"  # 改为其他端口
```

然后重新启动：

```bash
docker-compose down
docker-compose up -d
```

## 🔐 生产环境安全建议

1. **修改默认密码**
   - 修改管理员密码（在系统中）
   - 修改数据库密码（在 docker-compose.yml 和 .env 中）

2. **更新 SECRET_KEY**
   - 生成随机密钥：`openssl rand -hex 32`
   - 更新 `backend/.env` 中的 `SECRET_KEY`

3. **配置防火墙**
   ```bash
   # 只允许必要的端口
   ufw allow 22    # SSH
   ufw allow 80    # HTTP
   ufw allow 443   # HTTPS
   ufw enable
   ```

4. **使用反向代理**
   - 建议使用 Nginx 作为反向代理
   - 配置 SSL/TLS 证书

5. **限制 CORS**
   - 修改 `backend/app/main.py` 中的 CORS 配置
   - 将 `allow_origins=['*']` 改为具体的域名

## 📝 开发模式

如果需要开发调试，可以挂载源代码：

```bash
# 已在 docker-compose.yml 中配置
# backend/app 已挂载到容器内
# 修改代码后会自动重载（uvicorn --reload）
```

## 🌟 更新项目

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up --build -d

# 运行数据库迁移
docker exec -it yk_vos_backend alembic upgrade head
```

## 📞 技术支持

如有问题，请检查：
1. 所有容器是否正常运行
2. 日志文件中的错误信息
3. 环境变量配置是否正确
4. 网络连接是否正常

## 🎯 下一步

项目运行后，您可以：
1. 登录管理界面
2. 添加 VOS 实例
3. 查看在线话机
4. 查询历史话单
5. 配置定时同步任务

祝您使用愉快！🎉

