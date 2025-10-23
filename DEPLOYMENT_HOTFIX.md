# 部署错误修复说明

## 🐛 问题描述

**错误**: 后端容器启动失败，Alembic数据库迁移报错

```
ImportError: cannot import name 'Base' from 'app.core.db' (/srv/app/core/db.py)
```

**发生位置**: `backend/app/models/sync_config.py`

**影响**: 无法启动backend容器，数据库迁移失败

---

## ✅ 已修复

### 修复内容

**文件**: `backend/app/models/sync_config.py`

**错误代码** (第6行):
```python
from app.core.db import Base  # ❌ 错误
```

**正确代码**:
```python
from app.models.base import Base  # ✅ 正确
```

### 根本原因

在创建`SyncConfig`模型时，错误地从`app.core.db`导入了`Base`类。

在本项目中：
- ✅ `app.models.base.Base` - 正确的SQLAlchemy Base类
- ❌ `app.core.db.Base` - 不存在，`db.py`只导出数据库引擎和会话

---

## 🔧 配置调整

### TimescaleDB性能配置

**文件**: `docker-compose.yaml`

为适应不同服务器内存配置，已调整TimescaleDB参数：

#### 16GB服务器（原配置）
```yaml
TS_TUNE_MEMORY: "8GB"
TS_TUNE_NUM_CPUS: "4"
```

#### 8GB服务器（当前配置）
```yaml
TS_TUNE_MEMORY: "4GB"
TS_TUNE_NUM_CPUS: "2"
```

**说明**:
- `TS_TUNE_MEMORY`: 建议设置为服务器总内存的50%
- `TS_TUNE_NUM_CPUS`: 设置为CPU核心数或稍少
- `shm_size`: 保持2GB不变（TimescaleDB需要）

---

## 🚀 部署步骤

### 1. 拉取最新代码

```bash
cd /data/yk-vos
git pull origin main
```

### 2. 检查配置

确认`.env`文件配置正确：
```bash
cat .env
```

应该包含：
```env
POSTGRES_USER=vos_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=vosadmin
DATABASE_URL=postgresql://vos_user:your_password@postgres:5432/vosadmin
```

### 3. 清理并重启

```bash
# 停止所有容器
docker-compose down

# 清理旧镜像（可选）
docker-compose build --no-cache backend

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

### 4. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 应该看到所有容器都是 Up 状态
# yk_vos_timescaledb   Up (healthy)
# yk_vos_redis         Up (healthy)
# yk_vos_backend       Up
# yk_vos_frontend      Up
# yk_vos_celery_worker Up
# yk_vos_celery_beat   Up

# 检查数据库迁移
docker-compose exec backend alembic current

# 检查TimescaleDB
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dx timescaledb"

# 检查超表
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
    SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'cdrs';
"
```

### 5. 访问系统

```
前端: http://your-server-ip:3000
默认账号: admin / admin123
```

---

## 🔍 故障排查

### 问题1: 仍然报导入错误

**检查**:
```bash
# 确认代码已更新
docker-compose exec backend cat /srv/app/models/sync_config.py | grep "from app"

# 应该显示: from app.models.base import Base
```

**解决**:
```bash
# 强制重建镜像
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
```

### 问题2: 数据库连接失败

**检查**:
```bash
# 查看数据库日志
docker-compose logs postgres

# 测试连接
docker-compose exec postgres pg_isready -U vos_user -d vosadmin
```

**解决**:
```bash
# 检查.env文件
cat .env

# 检查数据库密码是否正确
docker-compose exec postgres psql -U vos_user -d vosadmin -c "SELECT version();"
```

### 问题3: Alembic迁移失败

**检查**:
```bash
# 查看迁移历史
docker-compose exec backend alembic history

# 查看当前版本
docker-compose exec backend alembic current

# 查看未应用的迁移
docker-compose exec backend alembic show head
```

**解决**:
```bash
# 手动运行迁移
docker-compose exec backend alembic upgrade head

# 如果失败，查看详细错误
docker-compose exec backend alembic upgrade head --verbose
```

### 问题4: TimescaleDB内存不足

**症状**: 数据库频繁重启或查询超时

**检查**:
```bash
# 查看容器内存使用
docker stats

# 查看PostgreSQL配置
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
    SHOW shared_buffers;
    SHOW effective_cache_size;
"
```

**解决**:

调整`docker-compose.yaml`中的内存配置：

**4GB服务器**:
```yaml
TS_TUNE_MEMORY: "2GB"
TS_TUNE_NUM_CPUS: "2"
shm_size: 1gb
```

**8GB服务器**:
```yaml
TS_TUNE_MEMORY: "4GB"
TS_TUNE_NUM_CPUS: "2"
shm_size: 2gb
```

**16GB服务器**:
```yaml
TS_TUNE_MEMORY: "8GB"
TS_TUNE_NUM_CPUS: "4"
shm_size: 2gb
```

---

## 📋 检查清单

部署前检查：

- [ ] 代码已拉取最新版本
- [ ] `.env`文件配置正确
- [ ] 数据库密码设置正确
- [ ] TimescaleDB内存配置适合服务器
- [ ] 数据目录权限正确（`data/postgres`）
- [ ] 端口未被占用（5430, 6379, 8000, 3000）

部署后验证：

- [ ] 所有容器都在运行
- [ ] 数据库健康检查通过
- [ ] Alembic迁移成功
- [ ] TimescaleDB扩展已安装
- [ ] `cdrs`超表已创建
- [ ] 前端可访问
- [ ] 可以正常登录

---

## 📚 相关文档

- **完整部署指南**: `TIMESCALEDB_DEPLOYMENT.md`
- **部署清单**: `DEPLOYMENT_CHECKLIST.md`
- **版本说明**: `V2_RELEASE_NOTES.md`
- **最终总结**: `FINAL_DEPLOYMENT_SUMMARY.md`

---

## 🎯 快速命令参考

```bash
# 查看所有容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 重启特定服务
docker-compose restart backend

# 完全重建
docker-compose down && docker-compose build --no-cache && docker-compose up -d

# 进入后端容器
docker-compose exec backend bash

# 进入数据库
docker-compose exec postgres psql -U vos_user -d vosadmin

# 查看数据库大小
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
    SELECT pg_size_pretty(pg_database_size('vosadmin'));
"

# 查看表结构
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\d+ cdrs"
```

---

**修复时间**: 2025-10-23  
**影响范围**: 仅backend容器启动  
**修复版本**: cb333ab

