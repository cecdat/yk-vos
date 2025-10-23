# TimescaleDB 全新部署清单

## 📋 部署前检查

### 服务器要求

- [ ] **操作系统**: Ubuntu 20.04+ 或 Debian 11+
- [ ] **内存**: 最少8GB，推荐16GB+
- [ ] **磁盘**: 最少50GB可用空间（SSD推荐）
- [ ] **CPU**: 4核+
- [ ] **网络**: 公网IP（如需外网访问）

### 软件要求

- [ ] **Docker**: 20.10+
- [ ] **Docker Compose**: 2.0+
- [ ] **Git**: 2.0+
- [ ] **端口开放**: 
  - 5430 (TimescaleDB)
  - 6379 (Redis)
  - 8000 (Backend API)
  - 3000 (Frontend)

---

## 🚀 快速部署（推荐）

### 步骤1: 连接服务器

```bash
# SSH连接到服务器
ssh root@your-server-ip

# 或使用密钥
ssh -i your-key.pem user@your-server-ip
```

### 步骤2: 安装Docker（如未安装）

```bash
# 卸载旧版本
sudo apt-get remove docker docker-engine docker.io containerd runc

# 更新apt包索引
sudo apt-get update

# 安装必要的依赖
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加Docker官方GPG密钥
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置Docker仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 验证安装
docker --version
docker compose version
```

### 步骤3: 克隆项目

```bash
# 创建项目目录
cd /data
sudo mkdir -p yk-vos
sudo chown -R $USER:$USER yk-vos

# 克隆代码（请替换为您的仓库地址）
git clone https://github.com/your-repo/yk-vos.git yk-vos
cd yk-vos
```

### 步骤4: 运行一键部署脚本

```bash
# 赋予执行权限
chmod +x init-deploy.sh

# 运行部署脚本
./init-deploy.sh
```

脚本会自动完成：
- ✅ 环境检查
- ✅ 创建.env配置文件
- ✅ 检测服务器IP
- ✅ 创建数据目录
- ✅ 构建基础镜像
- ✅ 启动所有服务
- ✅ 数据库迁移（自动创建TimescaleDB超表）
- ✅ 创建管理员账户
- ✅ 验证部署状态

### 步骤5: 验证部署

```bash
# 查看所有容器状态
docker compose ps

# 应该看到以下容器都在运行：
# - yk_vos_timescaledb
# - yk_vos_redis
# - yk_vos_backend
# - yk_vos_frontend
# - yk_vos_celery_worker
# - yk_vos_celery_beat

# 检查TimescaleDB扩展
docker compose exec postgres psql -U vos_user -d vosadmin -c "\dx timescaledb"

# 检查cdrs超表
docker compose exec postgres psql -U vos_user -d vosadmin -c "
    SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'cdrs';
"

# 查看后端日志
docker compose logs backend -f

# 访问前端
# http://your-server-ip:3000
# 默认账号: admin / admin123
```

---

## 🔧 手动部署（详细步骤）

### 1. 创建配置文件

```bash
cd /data/yk-vos

# 创建.env文件
cat > .env << 'EOF'
# 数据库配置
POSTGRES_USER=vos_user
POSTGRES_PASSWORD=CHANGE_THIS_SECURE_PASSWORD
POSTGRES_DB=vosadmin

# 应用配置
SECRET_KEY=CHANGE_THIS_TO_RANDOM_STRING_AT_LEAST_32_CHARS
DEBUG=False

# Redis配置
REDIS_URL=redis://redis:6379

# 数据库连接
DATABASE_URL=postgresql://vos_user:CHANGE_THIS_SECURE_PASSWORD@postgres:5432/vosadmin
EOF

# 修改密码和密钥
nano .env  # 或 vim .env
```

### 2. 创建数据目录

```bash
mkdir -p data/postgres
sudo chown -R 999:999 data/postgres  # PostgreSQL容器使用UID 999
```

### 3. 构建基础镜像

```bash
# 构建基础镜像（包含所有依赖）
docker compose -f docker-compose.base.yaml build

# 查看镜像
docker images | grep yk-vos
```

### 4. 启动服务

```bash
# 启动所有服务
docker compose up -d

# 查看启动日志
docker compose logs -f
```

### 5. 等待数据库初始化

```bash
# 等待TimescaleDB就绪
until docker compose exec postgres pg_isready -U vos_user -d vosadmin; do
    echo "等待TimescaleDB启动..."
    sleep 2
done

echo "✅ TimescaleDB已就绪"
```

### 6. 验证数据库迁移

```bash
# 查看后端日志，确认迁移成功
docker compose logs backend | grep -i "alembic\|migration"

# 应该看到类似：
# ✅ TimescaleDB超表创建成功！
# ✅ 已启用：
#   - 自动分区（每7天一个chunk）
#   - 自动压缩（30天后压缩，压缩比约10:1）
#   - 自动删除（1年后自动删除）
#   - 连续聚合（每小时统计）
```

### 7. 创建管理员账户

管理员账户会在容器启动时自动创建，默认账号：
- **用户名**: `admin`
- **密码**: `admin123`

⚠️ **首次登录后请立即修改密码！**

### 8. 配置防火墙（可选）

```bash
# 如果需要外网访问
sudo ufw allow 3000/tcp  # 前端
sudo ufw allow 8000/tcp  # 后端API（可选）

# 如果只允许内网访问，则不需要开放
```

---

## ✅ 部署验证清单

### 基础服务检查

- [ ] 所有容器都在运行: `docker compose ps`
- [ ] TimescaleDB可以连接: `docker compose exec postgres psql -U vos_user -d vosadmin -c "SELECT version();"`
- [ ] Redis可以连接: `docker compose exec redis redis-cli ping`
- [ ] 后端API响应: `curl http://localhost:8000/health`
- [ ] 前端可访问: `curl http://localhost:3000`

### TimescaleDB检查

- [ ] TimescaleDB扩展已安装:
  ```bash
  docker compose exec postgres psql -U vos_user -d vosadmin -c "\dx timescaledb"
  ```

- [ ] cdrs超表已创建:
  ```bash
  docker compose exec postgres psql -U vos_user -d vosadmin -c "
      SELECT hypertable_name, num_dimensions, compression_enabled
      FROM timescaledb_information.hypertables 
      WHERE hypertable_name = 'cdrs';
  "
  ```

- [ ] 压缩策略已配置:
  ```bash
  docker compose exec postgres psql -U vos_user -d vosadmin -c "
      SELECT * FROM timescaledb_information.jobs 
      WHERE proc_name LIKE '%compression%';
  "
  ```

- [ ] 保留策略已配置:
  ```bash
  docker compose exec postgres psql -U vos_user -d vosadmin -c "
      SELECT * FROM timescaledb_information.jobs 
      WHERE proc_name LIKE '%retention%';
  "
  ```

### 功能检查

- [ ] 登录系统: 访问 `http://your-server-ip:3000/login`
  - 用户名: `admin`
  - 密码: `admin123`

- [ ] 添加VOS节点: 系统设置 → VOS节点管理

- [ ] 查看话单: 话单历史页面

- [ ] 查看客户: 客户管理页面

---

## 🔐 安全加固（生产环境必做）

### 1. 修改默认密码

```bash
# 登录系统后，前往"系统设置"修改管理员密码
```

### 2. 修改数据库密码

```bash
# 1. 修改.env文件
nano .env
# 修改 POSTGRES_PASSWORD 和 DATABASE_URL

# 2. 重启服务
docker compose down
docker compose up -d
```

### 3. 启用防火墙

```bash
# 安装ufw
sudo apt-get install ufw

# 允许SSH
sudo ufw allow 22/tcp

# 允许前端（如果需要外网访问）
sudo ufw allow 3000/tcp

# 启用防火墙
sudo ufw enable
sudo ufw status
```

### 4. 配置HTTPS（推荐）

```bash
# 使用Nginx反向代理 + Let's Encrypt
sudo apt-get install nginx certbot python3-certbot-nginx

# 配置Nginx
sudo nano /etc/nginx/sites-available/yk-vos

# 添加配置（示例）
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# 启用配置
sudo ln -s /etc/nginx/sites-available/yk-vos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 申请SSL证书
sudo certbot --nginx -d your-domain.com
```

---

## 📊 性能优化（可选）

### 1. 调整TimescaleDB配置

```bash
# 编辑postgresql.conf
nano postgresql.conf

# 根据服务器内存调整：
# 8GB服务器:
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 128MB
maintenance_work_mem = 512MB

# 16GB服务器（默认）:
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 256MB
maintenance_work_mem = 1GB

# 重启服务使配置生效
docker compose restart postgres
```

### 2. 设置定期备份

```bash
# 创建备份脚本
cat > /data/yk-vos/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/data/backups/yk-vos"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
docker compose exec -T postgres pg_dump -U vos_user -d vosadmin | gzip > $BACKUP_DIR/vosadmin_$DATE.sql.gz

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "✅ 备份完成: $BACKUP_DIR/vosadmin_$DATE.sql.gz"
EOF

chmod +x /data/yk-vos/backup.sh

# 添加到crontab（每天凌晨2点备份）
(crontab -l 2>/dev/null; echo "0 2 * * * /data/yk-vos/backup.sh >> /var/log/yk-vos-backup.log 2>&1") | crontab -
```

---

## 🚨 常见问题

### 问题1: 容器无法启动

**检查日志**:
```bash
docker compose logs backend
docker compose logs postgres
```

**常见原因**:
- 端口冲突 → 修改docker-compose.yaml中的端口
- 数据目录权限 → `sudo chown -R 999:999 data/postgres`
- 内存不足 → 增加服务器内存或调整配置

### 问题2: 数据库迁移失败

**解决步骤**:
```bash
# 1. 查看迁移日志
docker compose logs backend | grep alembic

# 2. 手动运行迁移
docker compose exec backend alembic upgrade head

# 3. 如果失败，检查数据库连接
docker compose exec backend python -c "from app.core.db import engine; print(engine.url)"
```

### 问题3: 前端无法访问后端

**检查配置**:
```bash
# 查看前端环境变量
docker compose exec frontend env | grep API

# 应该看到：
# NEXT_PUBLIC_API_BASE=http://your-server-ip:8000/api/v1

# 如果不对，修改docker-compose.yaml，重启前端
docker compose restart frontend
```

---

## 📚 下一步

部署完成后，您可以：

1. **添加VOS节点**: 系统设置 → VOS节点管理
2. **配置同步**: 系统设置 → 数据同步配置
3. **查看文档**: 
   - `TIMESCALEDB_DEPLOYMENT.md` - TimescaleDB详细说明
   - `QUICK_REFERENCE_CDR.md` - 话单数据快速参考
   - `CDR_OPTIMIZATION_PLAN.md` - 性能优化方案

---

**部署支持**: 如遇问题，请查看项目README.md或提交Issue

**最后更新**: 2025-10-23

