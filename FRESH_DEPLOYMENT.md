# YK-VOS 全新部署指南 (ClickHouse 架构)

## 架构说明

本系统使用双数据库架构：
- **PostgreSQL**: 存储配置数据（用户、VOS实例、健康检查等）
- **ClickHouse**: 存储海量话单数据（CDR记录）

## 前置条件

1. Linux 服务器（推荐 Ubuntu 20.04+ / CentOS 8+）
2. Docker 和 Docker Compose 已安装
3. 至少 4GB 可用内存
4. 至少 20GB 可用磁盘空间

## 快速部署步骤

### 1. 拉取最新代码

```bash
cd /opt  # 或其他你想部署的目录
git clone https://github.com/cecdat/yk-vos.git
cd yk-vos
```

### 2. 运行一键部署脚本

```bash
bash deploy.sh
```

部署脚本会自动完成以下操作：
1. ✅ 创建数据目录结构（`data/postgres/`, `data/clickhouse/`）
2. ✅ 设置正确的目录权限（PostgreSQL: UID 999, ClickHouse: UID 101）
3. ✅ 生成 `.env` 配置文件（包含随机密码）
4. ✅ 检查 ClickHouse 初始化脚本
5. ✅ 构建 Docker 镜像（前端 + 后端）
6. ✅ 启动所有服务（PostgreSQL, ClickHouse, Redis, Backend, Frontend, Celery）
7. ✅ 等待服务就绪
8. ✅ 显示访问地址和数据库密码

### 3. 访问系统

部署完成后，你会看到类似以下输出：

```
╔══════════════════════════════════════════════════════╗
║             🎉 部署完成！                            ║
╚══════════════════════════════════════════════════════╝

📋 服务访问地址：
   前端:        http://localhost:3000
   后端API:     http://localhost:8000
   API文档:     http://localhost:8000/docs

🔐 数据库账号密码：
   PostgreSQL:
      用户名: vos_user
      密码:   [自动生成的随机密码]
   
   ClickHouse:
      用户名: vos_user
      密码:   [自动生成的随机密码]

📝 默认管理员账号：
   用户名: admin
   密码:   admin123
   ⚠️  首次登录后请立即修改密码！
```

**重要**: 请保存显示的数据库密码！

### 4. 首次登录配置

1. 访问 `http://服务器IP:3000`
2. 使用默认账号登录：`admin` / `admin123`
3. **立即修改管理员密码**
4. 配置 VOS 实例（设置 -> VOS 实例管理）

## 常见问题排查

### 问题 1: PostgreSQL 容器启动失败

**错误信息**:
```
ERROR: relation "vos_instances" does not exist
```

**原因**: 数据目录权限问题或旧数据残留

**解决方法**:

```bash
# 停止所有服务
docker-compose down -v

# 清理旧数据（⚠️ 会删除所有数据）
sudo rm -rf data/postgres/*
sudo rm -rf data/clickhouse/*

# 重新设置权限
sudo chown -R 999:999 data/postgres
sudo chown -R 101:101 data/clickhouse
sudo chmod -R 755 data/postgres data/clickhouse

# 重新部署
bash deploy.sh
```

### 问题 2: ClickHouse 连接失败

**检查方法**:

```bash
# 查看 ClickHouse 日志
docker-compose logs clickhouse

# 测试 ClickHouse 连接
docker-compose exec clickhouse clickhouse-client --query "SELECT 1"
```

### 问题 3: 数据库迁移失败

**检查方法**:

```bash
# 查看后端日志
docker-compose logs backend

# 手动运行迁移
docker-compose exec backend alembic upgrade head
```

## 数据管理

### 数据备份

```bash
# 备份 PostgreSQL
docker-compose exec postgres pg_dump -U vos_user vosadmin > backup_postgres_$(date +%Y%m%d).sql

# 备份 ClickHouse（导出为 SQL）
docker-compose exec clickhouse clickhouse-client --query "SELECT * FROM vos_cdrs.cdrs FORMAT TabSeparated" > backup_clickhouse_$(date +%Y%m%d).tsv

# 或者直接备份数据目录
sudo tar -czf backup_data_$(date +%Y%m%d).tar.gz data/
```

### 数据恢复

```bash
# 恢复 PostgreSQL
docker-compose exec -T postgres psql -U vos_user vosadmin < backup_postgres_20251024.sql

# 恢复 ClickHouse
docker-compose exec -T clickhouse clickhouse-client --query "INSERT INTO vos_cdrs.cdrs FORMAT TabSeparated" < backup_clickhouse_20251024.tsv
```

## 常用管理命令

```bash
# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f clickhouse
docker-compose logs -f postgres

# 重启服务
docker-compose restart

# 重启特定服务
docker-compose restart backend

# 停止服务
docker-compose down

# 完全清理（包括数据卷）⚠️ 危险操作
docker-compose down -v
```

## 性能优化建议

### ClickHouse 优化

1. **内存配置**: 如果服务器内存充足（16GB+），可在 `docker-compose.yaml` 中增加 ClickHouse 内存限制：

```yaml
clickhouse:
  # ...
  deploy:
    resources:
      limits:
        memory: 8G
```

2. **数据压缩**: ClickHouse 默认已启用压缩，通常可达到 10:1 的压缩比

3. **分区管理**: CDR 表按月自动分区，旧数据分区可以定期清理：

```sql
-- 删除 2023 年的数据
ALTER TABLE vos_cdrs.cdrs DROP PARTITION '202301';
ALTER TABLE vos_cdrs.cdrs DROP PARTITION '202302';
-- ...
```

### PostgreSQL 优化

配置文件已包含基础优化，如需进一步调整，可修改 `data/postgres/postgresql.conf`

## 安全建议

1. **修改默认密码**: 
   - 管理员账号密码
   - 数据库密码（在 `.env` 中已自动生成随机密码）

2. **防火墙配置**:

```bash
# 仅允许必要的端口
sudo ufw allow 22    # SSH
sudo ufw allow 3000  # 前端
sudo ufw allow 8000  # 后端API（可选，建议通过 Nginx 反向代理）
sudo ufw enable
```

3. **配置 HTTPS**: 建议使用 Nginx 作为反向代理并配置 SSL 证书

## 监控和告警

### 服务健康检查

```bash
# 检查所有服务健康状态
docker-compose ps

# 检查 API 健康
curl http://localhost:8000/health

# 检查 ClickHouse
docker-compose exec clickhouse clickhouse-client --query "SELECT 1"
```

### 磁盘空间监控

```bash
# 查看数据目录占用
du -sh data/*

# 设置定时任务监控磁盘空间
crontab -e
# 添加：0 1 * * * /usr/bin/du -sh /opt/yk-vos/data/* >> /var/log/yk-vos-disk.log
```

## 升级指南

### 代码更新

```bash
cd /opt/yk-vos
git pull origin main
docker-compose down
docker-compose -f docker-compose.base.yaml build
docker-compose up -d
```

### 数据库迁移

数据库迁移会在服务启动时自动执行（通过 `docker-entrypoint-clickhouse.sh`）

如需手动执行：

```bash
docker-compose exec backend alembic upgrade head
```

## 故障排查清单

### ✅ 服务启动检查清单

- [ ] Docker 和 Docker Compose 已安装
- [ ] 数据目录权限正确（postgres: 999, clickhouse: 101）
- [ ] 端口未被占用（3000, 8000, 5430, 9000, 8123, 6379）
- [ ] 磁盘空间充足（至少 20GB）
- [ ] `.env` 文件存在且包含正确配置
- [ ] `clickhouse/init/01_create_tables.sql` 文件存在

### 🔍 日志检查优先级

1. **后端日志**: `docker-compose logs backend` - 查看 API 错误和数据库连接
2. **PostgreSQL 日志**: `docker-compose logs postgres` - 查看 SQL 错误
3. **ClickHouse 日志**: `docker-compose logs clickhouse` - 查看话单存储错误
4. **Celery 日志**: `docker-compose logs celery-worker` - 查看异步任务错误

## 技术支持

如遇到问题，请提供以下信息：

1. 操作系统版本：`uname -a`
2. Docker 版本：`docker --version`
3. Docker Compose 版本：`docker-compose --version`
4. 服务状态：`docker-compose ps`
5. 相关日志：`docker-compose logs [service_name]`

---

**最后更新**: 2025-10-24  
**架构版本**: ClickHouse v1.0  
**兼容版本**: Docker 20.10+, Docker Compose 2.0+

