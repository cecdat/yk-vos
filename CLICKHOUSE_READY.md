# ✅ ClickHouse 架构完整实施 - 就绪清单

## 🎉 已完成的工作

### 📁 核心代码模块

✅ **ClickHouse 连接模块** (`backend/app/core/clickhouse_db.py`)
- 单例模式连接管理
- 自动重连机制
- 查询/插入/Ping功能
- 完整的错误处理

✅ **ClickHouse CDR 操作类** (`backend/app/models/clickhouse_cdr.py`)
- `insert_cdrs()`: 批量插入话单
- `query_cdrs()`: 查询话单（支持分页、过滤）
- `get_stats()`: 统计信息
- `delete_old_partitions()`: 自动清理旧数据

✅ **CDR 路由更新** (`backend/app/routers/cdr.py`)
- 查询优先使用 ClickHouse
- VOS API 数据自动存入 ClickHouse
- 导出功能使用 ClickHouse
- 完整的降级策略

### 🗂️ 数据库配置

✅ **建表脚本** (`clickhouse/init/01_create_tables.sql`)
- cdrs 主表（ReplacingMergeTree，自动去重）
- 按月自动分区
- 4 个跳数索引
- 3 个物化视图（日统计、账户统计、网关统计）

✅ **Docker Compose 配置** (`docker-compose.clickhouse.yaml`)
- 7 个服务完整配置
- 数据本地映射：`./data/clickhouse` 和 `./data/postgres`
- 健康检查和依赖关系
- 环境变量配置

### 🚀 部署脚本

✅ **一键部署脚本** (`deploy-clickhouse.sh`)
- 自动创建目录
- 自动设置权限
- 环境检查
- 服务启动
- 健康检查
- **账号密码输出** ⭐

✅ **启动脚本** (`backend/docker-entrypoint-clickhouse.sh`)
- 等待 PostgreSQL 和 ClickHouse
- 数据库迁移
- 管理员账户初始化
- ClickHouse 连接测试
- **配置信息输出（含密码）** ⭐

### 📚 完整文档

✅ `CLICKHOUSE_MIGRATION.md` - 迁移概述
✅ `CLICKHOUSE_IMPLEMENTATION_GUIDE.md` - 实施指南
✅ `DATA_STORAGE.md` - 数据存储说明
✅ `CLICKHOUSE_READY.md` - 就绪清单（本文档）

## 🔐 账号密码

### 默认账号密码（首次部署）

**PostgreSQL（配置数据）：**
```
用户名: vos_user
密码:   vos_password_change_me
```

**ClickHouse（话单数据）：**
```
用户名: vos_user
密码:   clickhouse_password_change_me
```

### 查看实际密码

**方法 1：查看 .env 文件**
```bash
cd /data/yk-vos
cat .env
```

**方法 2：部署完成时自动显示**
```bash
./deploy-clickhouse.sh
# 部署完成后会显示所有账号密码
```

**方法 3：查看容器日志**
```bash
docker-compose -f docker-compose.clickhouse.yaml logs backend | grep "数据库配置"
```

## 🚀 服务器部署步骤

### 完整部署流程

```bash
# 1. 进入项目目录
cd /data/yk-vos

# 2. 拉取最新代码
git pull

# 3. 赋予脚本执行权限
chmod +x deploy-clickhouse.sh

# 4. 执行一键部署
./deploy-clickhouse.sh

# 脚本会自动完成：
# ✅ 创建目录结构
# ✅ 设置权限（ClickHouse: 101, PostgreSQL: 999）
# ✅ 生成 .env 配置文件
# ✅ 启动所有服务
# ✅ 健康检查
# ✅ 显示账号密码 ⭐

# 5. 查看服务状态
docker-compose -f docker-compose.clickhouse.yaml ps

# 6. 查看日志
docker-compose -f docker-compose.clickhouse.yaml logs -f
```

### 修改默认密码（重要！）

```bash
# 编辑 .env 文件
nano .env

# 修改以下内容：
POSTGRES_PASSWORD=your_secure_password_here
CLICKHOUSE_PASSWORD=your_secure_password_here
SECRET_KEY=your_random_secret_key_here

# 保存后重启服务
docker-compose -f docker-compose.clickhouse.yaml down
docker-compose -f docker-compose.clickhouse.yaml up -d
```

## 📊 验证部署

### 1. 检查服务状态

```bash
docker-compose -f docker-compose.clickhouse.yaml ps

# 应该看到 7 个服务都是 Up 状态：
# - postgres
# - clickhouse
# - redis
# - backend
# - frontend
# - celery-worker
# - celery-beat
```

### 2. 测试 ClickHouse

```bash
# 进入 ClickHouse 客户端
docker-compose -f docker-compose.clickhouse.yaml exec clickhouse clickhouse-client

# 查看数据库
SHOW DATABASES;

# 查看表
SHOW TABLES FROM vos_cdrs;

# 应该看到：
# cdrs
# cdrs_account_stats
# cdrs_daily_stats
# cdrs_gateway_stats

# 退出
exit
```

### 3. 测试 API

```bash
# 测试健康检查
curl http://localhost:8000/health

# 测试 API 文档
curl http://localhost:8000/docs
# 或在浏览器打开: http://服务器IP:8000/docs
```

### 4. 访问前端

```
浏览器打开: http://服务器IP:3000
默认管理员账号: admin
默认密码: admin123
```

## 📈 数据迁移（可选）

### 如果有旧数据需要迁移

```bash
# 1. 导出旧数据（PostgreSQL）
docker-compose exec postgres pg_dump -U vos_user -d vosadmin -t cdrs > cdrs_backup.sql

# 2. 转换并导入 ClickHouse
# 编写转换脚本或手动导入
# 详见 CLICKHOUSE_IMPLEMENTATION_GUIDE.md
```

## 🎯 查询性能对比

### 测试查询

```sql
-- 查询最近7天的话单
SELECT COUNT(*) FROM cdrs 
WHERE start >= now() - INTERVAL 7 DAY;

-- 按账户统计
SELECT account, COUNT(*), SUM(fee) 
FROM cdrs 
WHERE start >= now() - INTERVAL 30 DAY
GROUP BY account
ORDER BY COUNT(*) DESC
LIMIT 10;
```

### 预期性能

| 数据量 | PostgreSQL | ClickHouse | 提升 |
|--------|-----------|------------|------|
| 100万 | 2秒 | 100ms | 20倍 |
| 1000万 | 30秒 | 500ms | 60倍 |
| 1亿 | 5分钟+ | 2-3秒 | 100倍+ |

## 🔧 常用管理命令

### 服务管理

```bash
# 查看服务状态
docker-compose -f docker-compose.clickhouse.yaml ps

# 查看日志
docker-compose -f docker-compose.clickhouse.yaml logs -f

# 重启服务
docker-compose -f docker-compose.clickhouse.yaml restart

# 停止服务
docker-compose -f docker-compose.clickhouse.yaml down

# 启动服务
docker-compose -f docker-compose.clickhouse.yaml up -d
```

### 数据库管理

```bash
# ClickHouse 客户端
docker-compose -f docker-compose.clickhouse.yaml exec clickhouse clickhouse-client

# PostgreSQL 客户端
docker-compose -f docker-compose.clickhouse.yaml exec postgres psql -U vos_user -d vosadmin

# 查看数据量
docker-compose -f docker-compose.clickhouse.yaml exec clickhouse clickhouse-client --query "SELECT COUNT(*) FROM vos_cdrs.cdrs"
```

### 数据备份

```bash
# 备份所有数据
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz data/

# 恢复
tar -xzf backup-20251024-103000.tar.gz
```

## 📝 账号密码管理最佳实践

### 1. 首次部署后立即修改密码

```bash
# 编辑 .env
nano .env

# 修改所有密码为强密码（至少16位，包含大小写字母、数字、特殊字符）
POSTGRES_PASSWORD=$(openssl rand -base64 24)
CLICKHOUSE_PASSWORD=$(openssl rand -base64 24)
SECRET_KEY=$(openssl rand -base64 32)
```

### 2. 保存密码到安全位置

- 使用密码管理器（如 1Password、LastPass）
- 加密保存到云端
- 备份到离线存储

### 3. 定期更换密码

建议每 3-6 个月更换一次数据库密码。

### 4. 限制访问权限

```bash
# 设置 .env 文件权限
chmod 600 .env
chown root:root .env
```

## ⚠️ 注意事项

1. **首次部署必须修改默认密码**
2. **定期备份数据**（建议每天备份）
3. **监控磁盘空间**（建议保留 30% 空间）
4. **定期清理旧分区**（保留 12 个月数据）
5. **关注服务日志**，及时发现问题

## 🎯 下一步

1. ✅ 修改默认密码
2. ✅ 测试话单查询功能
3. ✅ 测试导出功能
4. ✅ 设置监控告警
5. ✅ 配置自动备份

## 🆘 问题排查

### ClickHouse 无法启动

```bash
# 检查日志
docker-compose -f docker-compose.clickhouse.yaml logs clickhouse

# 检查权限
sudo chown -R 101:101 data/clickhouse
```

### 查询报错

```bash
# 检查 ClickHouse 连接
docker-compose -f docker-compose.clickhouse.yaml exec backend python3 -c "
from app.core.clickhouse_db import get_clickhouse_db
print(get_clickhouse_db().ping())
"
```

### 性能问题

```bash
# 优化表
docker-compose -f docker-compose.clickhouse.yaml exec clickhouse clickhouse-client --query "OPTIMIZE TABLE vos_cdrs.cdrs FINAL"
```

## 📞 技术支持

遇到问题请查阅：
- `CLICKHOUSE_IMPLEMENTATION_GUIDE.md` - 详细技术文档
- `DATA_STORAGE.md` - 数据存储说明
- GitHub Issues - 提交问题

---

**🎉 恭喜！ClickHouse 架构已完全就绪，可以开始使用了！**


