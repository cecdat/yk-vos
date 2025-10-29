# YK-VOS 部署指南

## 概述

YK-VOS 是一个基于 FastAPI + Next.js 的 VOS3000 管理系统，支持 VOS 节点的统一管理、数据同步、话单查询等功能。

## 系统要求

### 硬件要求
- **CPU**: 2核心以上
- **内存**: 4GB以上
- **存储**: 50GB以上可用空间
- **网络**: 稳定的网络连接

### 软件要求
- **操作系统**: Ubuntu 20.04+, CentOS 7+, Debian 10+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

## 部署方式

### 方式一：全新安装（推荐新服务器）

适用于没有现有数据的全新服务器部署。

#### 1. 下载安装脚本
```bash
# 下载安装脚本
wget https://raw.githubusercontent.com/your-repo/yk-vos/main/scripts/fresh_install.sh
chmod +x fresh_install.sh
```

#### 2. 执行安装
```bash
# 执行安装脚本
sudo ./fresh_install.sh
```

#### 3. 配置Git仓库（可选）
如果需要从Git仓库自动下载代码：
```bash
export GIT_REPO="https://github.com/your-repo/yk-vos.git"
sudo ./fresh_install.sh
```

### 方式二：升级迁移（已有数据）

适用于已有数据的服务器升级到新版本。

#### 1. 下载升级脚本
```bash
# 下载升级脚本
wget https://raw.githubusercontent.com/your-repo/yk-vos/main/scripts/upgrade_migration.sh
chmod +x upgrade_migration.sh
```

#### 2. 执行升级
```bash
# 执行升级脚本
sudo ./upgrade_migration.sh
```

### 方式三：手动部署

#### 1. 安装Docker和Docker Compose
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin

# CentOS/RHEL
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo yum install docker-compose-plugin
```

#### 2. 下载项目代码
```bash
# 创建项目目录
sudo mkdir -p /opt/yk-vos
cd /opt/yk-vos

# 克隆代码
git clone https://github.com/your-repo/yk-vos.git .

# 或者下载压缩包
wget https://github.com/your-repo/yk-vos/archive/main.zip
unzip main.zip
mv yk-vos-main/* .
```

#### 3. 配置环境变量
```bash
# 创建环境变量文件
cat > .env << EOF
# 数据库配置
POSTGRES_DB=yk_vos
POSTGRES_USER=yk_vos_user
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Redis配置
REDIS_PASSWORD=$(openssl rand -base64 32)

# JWT配置
JWT_SECRET_KEY=$(openssl rand -base64 64)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=3001
FRONTEND_PORT=3000

# 时区
TZ=Asia/Shanghai
EOF
```

#### 4. 启动服务
```bash
# 构建并启动服务
docker compose up -d --build

# 等待服务启动
sleep 60

# 检查服务状态
docker compose ps
```

#### 5. 初始化数据库
```bash
# 执行数据库初始化脚本
docker compose exec -T postgres psql -U yk_vos_user -d yk_vos < sql/base.sql
docker compose exec -T postgres psql -U yk_vos_user -d yk_vos < sql/insert_user_agents.sql

# 初始化ClickHouse
docker compose exec -T clickhouse clickhouse-client < clickhouse/init/01_create_tables.sql
```

## 配置说明

### 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `POSTGRES_DB` | PostgreSQL数据库名 | `yk_vos` |
| `POSTGRES_USER` | PostgreSQL用户名 | `yk_vos_user` |
| `POSTGRES_PASSWORD` | PostgreSQL密码 | 随机生成 |
| `REDIS_PASSWORD` | Redis密码 | 随机生成 |
| `JWT_SECRET_KEY` | JWT密钥 | 随机生成 |
| `JWT_ALGORITHM` | JWT算法 | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | JWT过期时间(分钟) | `30` |
| `BACKEND_PORT` | 后端端口 | `3001` |
| `FRONTEND_PORT` | 前端端口 | `3000` |

### 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 3000 | Web界面 |
| 后端 | 3001 | API服务 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |
| ClickHouse | 8123 | 话单数据库 |

### 防火墙配置

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 3000/tcp
sudo ufw allow 3001/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --permanent --add-port=3001/tcp
sudo firewall-cmd --reload
```

## 服务管理

### 系统服务管理

安装脚本会自动创建系统服务，可以使用以下命令管理：

```bash
# 启动服务
sudo systemctl start yk-vos

# 停止服务
sudo systemctl stop yk-vos

# 重启服务
sudo systemctl restart yk-vos

# 查看状态
sudo systemctl status yk-vos

# 开机自启
sudo systemctl enable yk-vos
```

### Docker Compose管理

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 启动服务
docker compose up -d

# 重新构建
docker compose up -d --build
```

## 数据备份与恢复

### 数据备份

```bash
# 备份PostgreSQL数据库
docker compose exec -T postgres pg_dump -U yk_vos_user yk_vos > backup_$(date +%Y%m%d).sql

# 备份Redis数据
docker compose exec -T redis redis-cli --rdb backup_$(date +%Y%m%d).rdb

# 备份ClickHouse数据
docker compose exec -T clickhouse clickhouse-client --query "BACKUP DATABASE vos_cdrs TO Disk('backups', 'vos_cdrs_backup_$(date +%Y%m%d)')"
```

### 数据恢复

```bash
# 恢复PostgreSQL数据库
docker compose exec -T postgres psql -U yk_vos_user -d yk_vos < backup_20240101.sql

# 恢复Redis数据
docker compose exec -T redis redis-cli --rdb backup_20240101.rdb

# 恢复ClickHouse数据
docker compose exec -T clickhouse clickhouse-client --query "RESTORE DATABASE vos_cdrs FROM Disk('backups', 'vos_cdrs_backup_20240101')"
```

## 故障排除

### 常见问题

#### 1. 服务启动失败
```bash
# 查看详细日志
docker compose logs

# 检查端口占用
netstat -tlnp | grep :3000
netstat -tlnp | grep :3001

# 检查磁盘空间
df -h
```

#### 2. 数据库连接失败
```bash
# 检查PostgreSQL状态
docker compose exec postgres pg_isready -U yk_vos_user -d yk_vos

# 检查Redis状态
docker compose exec redis redis-cli ping

# 检查ClickHouse状态
docker compose exec clickhouse clickhouse-client --query "SELECT 1"
```

#### 3. 前端无法访问
```bash
# 检查前端服务
curl http://localhost:3000

# 检查后端API
curl http://localhost:3001/health

# 检查防火墙
sudo ufw status
```

### 日志查看

```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres
```

### 性能监控

```bash
# 查看资源使用情况
docker stats

# 查看磁盘使用
docker system df

# 清理无用数据
docker system prune -a
```

## 升级指南

### 自动升级

使用升级脚本进行自动升级：

```bash
sudo ./upgrade_migration.sh
```

### 手动升级

1. **备份数据**
```bash
# 执行数据备份
./scripts/backup_data.sh
```

2. **停止服务**
```bash
docker compose down
```

3. **更新代码**
```bash
git pull origin main
```

4. **更新镜像**
```bash
docker compose pull
docker compose build --no-cache
```

5. **执行数据库迁移**
```bash
# 执行升级脚本
docker compose exec -T postgres psql -U yk_vos_user -d yk_vos < sql/upgrade_db_v2.3.sql
```

6. **启动服务**
```bash
docker compose up -d
```

## 安全配置

### 1. 修改默认密码
```bash
# 登录系统后立即修改默认密码
# 默认账号: admin / admin123
```

### 2. 配置HTTPS（可选）
```bash
# 使用Nginx反向代理配置SSL
# 参考: nginx/ssl.conf
```

### 3. 限制访问
```bash
# 配置防火墙只允许特定IP访问
sudo ufw allow from 192.168.1.0/24 to any port 3000
sudo ufw allow from 192.168.1.0/24 to any port 3001
```

## 监控与维护

### 1. 健康检查
```bash
# 检查服务健康状态
curl http://localhost:3001/health

# 检查数据库连接
docker compose exec postgres pg_isready -U yk_vos_user -d yk_vos
```

### 2. 定期维护
```bash
# 清理过期日志
docker system prune -f

# 更新系统包
sudo apt update && sudo apt upgrade -y

# 重启服务
sudo systemctl restart yk-vos
```

### 3. 性能优化
```bash
# 调整PostgreSQL配置
# 参考: postgresql/postgresql.conf

# 调整Redis配置
# 参考: redis/redis.conf

# 调整ClickHouse配置
# 参考: clickhouse/config.xml
```

## 联系支持

如遇到问题，请提供以下信息：

1. 操作系统版本
2. Docker版本
3. 错误日志
4. 服务状态
5. 网络配置

联系方式：
- 邮箱: support@example.com
- 文档: https://docs.example.com
- 问题反馈: https://github.com/your-repo/yk-vos/issues