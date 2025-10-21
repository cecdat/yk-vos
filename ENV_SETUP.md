# 环境变量配置说明

本项目需要配置环境变量才能正常运行。请按照以下步骤设置。

## 后端环境变量

创建 `backend/.env` 文件：

```bash
cd backend
cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://vos:vos123@db:5432/vosdb

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# JWT Secret Key (生产环境务必修改！)
SECRET_KEY=yk-vos-secret-key-2025-change-in-production

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=YK-VOS API

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF
```

### 重要说明

1. **SECRET_KEY**: 在生产环境中，必须使用强随机密钥
   ```bash
   # 生成随机密钥
   openssl rand -hex 32
   ```

2. **DATABASE_URL**: 
   - 格式: `postgresql://用户名:密码@主机:端口/数据库名`
   - Docker 环境使用服务名 `db` 作为主机名
   - 如果是外部数据库，修改为实际的 IP 地址

3. **REDIS_URL**: 
   - 格式: `redis://主机:端口/数据库编号`
   - Docker 环境使用服务名 `redis` 作为主机名

## 前端环境变量

创建 `frontend/.env` 文件：

```bash
cd frontend
cat > .env << 'EOF'
# API Base URL
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
EOF
```

### 重要说明

1. **开发环境**: 使用 `http://localhost:8000/api/v1`
2. **Docker 环境**: 使用 `http://backend:8000/api/v1`
3. **生产环境**: 修改为实际服务器地址
   ```env
   NEXT_PUBLIC_API_BASE=http://YOUR_SERVER_IP:8000/api/v1
   ```
   或使用域名：
   ```env
   NEXT_PUBLIC_API_BASE=https://api.yourdomain.com/api/v1
   ```

## 快速配置脚本（Linux/Mac）

在项目根目录执行：

```bash
#!/bin/bash

# 后端环境变量
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://vos:vos123@db:5432/vosdb
REDIS_URL=redis://redis:6379/0
SECRET_KEY=yk-vos-secret-key-2025-change-in-production
API_V1_PREFIX=/api/v1
PROJECT_NAME=YK-VOS API
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF

# 前端环境变量（根据需要修改 API 地址）
cat > frontend/.env << 'EOF'
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
EOF

echo "✅ 环境变量配置完成！"
echo "⚠️  请记得修改 SECRET_KEY 为随机值！"
```

## Windows PowerShell 配置脚本

```powershell
# 后端环境变量
@"
DATABASE_URL=postgresql://vos:vos123@db:5432/vosdb
REDIS_URL=redis://redis:6379/0
SECRET_KEY=yk-vos-secret-key-2025-change-in-production
API_V1_PREFIX=/api/v1
PROJECT_NAME=YK-VOS API
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
"@ | Out-File -FilePath backend\.env -Encoding utf8

# 前端环境变量
@"
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
"@ | Out-File -FilePath frontend\.env -Encoding utf8

Write-Host "✅ 环境变量配置完成！"
Write-Host "⚠️  请记得修改 SECRET_KEY 为随机值！"
```

## 验证配置

配置完成后，检查文件是否存在：

```bash
# 检查后端环境变量
ls -la backend/.env

# 检查前端环境变量
ls -la frontend/.env

# 查看内容
cat backend/.env
cat frontend/.env
```

## 不同部署场景的配置

### 场景 1: 本地开发

```env
# backend/.env
DATABASE_URL=postgresql://vos:vos123@localhost:5432/vosdb
REDIS_URL=redis://localhost:6379/0

# frontend/.env
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
```

### 场景 2: Docker Compose（推荐）

```env
# backend/.env
DATABASE_URL=postgresql://vos:vos123@db:5432/vosdb
REDIS_URL=redis://redis:6379/0

# frontend/.env
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
```

### 场景 3: 生产服务器

```env
# backend/.env
DATABASE_URL=postgresql://vos:SecurePassword123@db:5432/vosdb
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<使用 openssl rand -hex 32 生成的随机密钥>

# frontend/.env
NEXT_PUBLIC_API_BASE=http://192.168.1.100:8000/api/v1
# 或使用域名
NEXT_PUBLIC_API_BASE=https://api.yourdomain.com/api/v1
```

## 安全建议

1. ✅ 永远不要将 `.env` 文件提交到 Git
2. ✅ 在生产环境中使用强密码和随机密钥
3. ✅ 定期更新密钥和密码
4. ✅ 限制数据库和 Redis 的访问权限
5. ✅ 在生产环境中使用 HTTPS

## 常见问题

### Q: 为什么无法连接数据库？
A: 检查 `DATABASE_URL` 是否正确，特别是主机名（Docker 环境使用 `db`，本地开发使用 `localhost`）

### Q: 前端无法访问 API？
A: 检查 `NEXT_PUBLIC_API_BASE` 的地址是否正确，确保后端服务已启动并可访问

### Q: Celery 任务不执行？
A: 检查 `REDIS_URL` 是否正确，确保 Redis 服务正常运行

### Q: JWT 认证失败？
A: 检查 `SECRET_KEY` 是否在所有服务中保持一致

## 下一步

配置完成后，请参考 [SETUP_GUIDE.md](./SETUP_GUIDE.md) 继续部署项目。

