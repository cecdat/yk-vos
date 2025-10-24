# YK-VOS 部署指南

## 🚀 快速部署

### 使用部署工具（推荐）

```bash
bash deploy.sh
```

部署工具提供交互式菜单：

```
╔════════════════════════════════════════════════╗
║                                                ║
║        YK-VOS 部署工具                         ║
║                                                ║
╚════════════════════════════════════════════════╝

请选择操作：

  1) 快速更新 (拉代码 + 迁移 + 重启服务)
  2) 完整升级 (备份 + 拉代码 + 重建 + 迁移 + 重启)
  3) 仅重启服务
  4) 数据库迁移 (检查并执行)
  5) 查看迁移状态
  6) 查看服务状态
  7) 查看日志
  0) 退出
```

### 各选项说明

#### 选项1：快速更新
**适用场景**：日常代码更新，功能迭代

**执行步骤**：
1. ✅ 拉取最新代码
2. ✅ 自动执行数据库迁移
3. ✅ 重启相关服务
4. ✅ 健康检查

**优点**：
- 快速，约30秒完成
- 自动处理数据库迁移
- 有失败确认机制

**使用示例**：
```bash
bash deploy.sh
# 选择 1
```

#### 选项2：完整升级
**适用场景**：
- 重大版本升级
- 依赖包更新
- 首次部署

**执行步骤**：
1. ✅ 备份数据库
2. ✅ 拉取最新代码
3. ✅ 停止服务
4. ✅ 重新构建基础镜像
5. ✅ 启动数据库和缓存
6. ✅ 启动后端并执行迁移
7. ✅ 启动所有服务
8. ✅ 健康检查

**优点**：
- 完整的升级流程
- 自动备份防止数据丢失
- 重建镜像确保依赖更新

**使用示例**：
```bash
bash deploy.sh
# 选择 2
# 确认继续 y
```

#### 选项3：仅重启服务
**适用场景**：配置文件修改后重启

```bash
bash deploy.sh
# 选择 3
```

#### 选项4：数据库迁移
**适用场景**：
- 单独执行数据库升级
- 迁移失败后重试
- 验证迁移状态

**功能**：
- ✅ 检查数据库连接
- ✅ 显示当前迁移版本
- ✅ 执行迁移到最新版本
- ✅ 显示迁移后状态
- ✅ 失败时给出建议

**使用示例**：
```bash
bash deploy.sh
# 选择 4
```

#### 选项5：查看迁移状态
**显示内容**：
- 当前迁移版本
- 迁移历史记录
- 数据库表列表

```bash
bash deploy.sh
# 选择 5
```

#### 选项6：查看服务状态
**检查项目**：
- ✅ Docker容器状态
- ✅ 后端服务健康检查
- ✅ 前端服务健康检查
- ✅ 数据库连接状态
- ✅ Redis连接状态

```bash
bash deploy.sh
# 选择 6
```

#### 选项7：查看日志
**可查看的日志**：
1. 后端日志
2. 前端日志
3. Celery Worker日志
4. Celery Beat日志
5. 所有服务日志

```bash
bash deploy.sh
# 选择 7
# 然后选择要查看的日志
```

## 🛠️ 手动部署

### 首次部署

```bash
# 1. 克隆项目
git clone <repository-url>
cd yk-vos

# 2. 创建环境变量文件
cp .env.example .env
# 编辑 .env 文件，设置必要的配置

# 3. 构建基础镜像
docker-compose -f docker-compose.base.yaml build

# 4. 启动服务
docker-compose up -d

# 5. 查看日志确认启动成功
docker-compose logs -f backend
```

### 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 如果依赖有更新，重建基础镜像
docker-compose -f docker-compose.base.yaml build

# 3. 重启服务（数据库迁移会自动执行）
docker-compose restart backend celery-worker celery-beat frontend
```

## 📋 数据库迁移

详见 [DATABASE_MIGRATION.md](DATABASE_MIGRATION.md)

### 快速参考

```bash
# 查看迁移状态
docker-compose exec backend alembic current

# 执行迁移
docker-compose exec backend alembic upgrade head

# 回滚一个版本
docker-compose exec backend alembic downgrade -1

# 查看迁移历史
docker-compose exec backend alembic history
```

## 🔍 健康检查

### 检查所有服务

```bash
bash deploy.sh
# 选择 6
```

或手动检查：

```bash
# 容器状态
docker-compose ps

# 后端健康检查
curl http://localhost:8000/health

# 前端检查
curl -I http://localhost:3000

# 数据库检查
docker-compose exec postgres pg_isready -U vos_user -d vosadmin

# Redis检查
docker-compose exec redis redis-cli ping
```

### 查看日志

```bash
# 查看所有日志
docker-compose logs -f

# 查看特定服务
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat

# 查看最近50条日志
docker-compose logs --tail=50 backend
```

## 💾 备份与恢复

### 自动备份

使用部署工具的"完整升级"选项会自动备份：

```bash
bash deploy.sh
# 选择 2
```

备份文件格式：`backup_YYYYMMDD_HHMMSS.sql`

### 手动备份

```bash
# 完整备份
docker exec yk_vos_timescaledb pg_dump -U vos_user -d vosadmin > backup_$(date +%Y%m%d_%H%M%S).sql

# 压缩备份
docker exec yk_vos_timescaledb pg_dump -U vos_user -d vosadmin | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 恢复备份

```bash
# 恢复普通备份
cat backup_20251024_120000.sql | docker exec -i yk_vos_timescaledb psql -U vos_user -d vosadmin

# 恢复压缩备份
gunzip -c backup_20251024_120000.sql.gz | docker exec -i yk_vos_timescaledb psql -U vos_user -d vosadmin
```

## 🔧 故障排查

### 服务无法启动

```bash
# 1. 查看日志
docker-compose logs backend

# 2. 检查数据库连接
docker-compose exec postgres pg_isready

# 3. 检查端口占用
netstat -tuln | grep -E '3000|8000|5432|6379'

# 4. 重新构建并启动
docker-compose down
docker-compose -f docker-compose.base.yaml build
docker-compose up -d
```

### 数据库迁移失败

```bash
# 1. 查看迁移状态
docker-compose exec backend alembic current

# 2. 查看详细错误
docker-compose exec backend alembic upgrade head --verbose

# 3. 如需回滚
docker-compose exec backend alembic downgrade -1

# 4. 恢复备份
cat backup_latest.sql | docker exec -i yk_vos_timescaledb psql -U vos_user -d vosadmin
```

### 前端打包失败

```bash
# 1. 清理缓存
docker-compose exec frontend rm -rf .next node_modules

# 2. 重建前端镜像
docker-compose -f docker-compose.base.yaml build frontend

# 3. 重启服务
docker-compose restart frontend
```

## 📊 监控和维护

### 定期任务

```bash
# 每周备份一次数据库
0 2 * * 0 docker exec yk_vos_timescaledb pg_dump -U vos_user -d vosadmin | gzip > /backups/weekly_$(date +\%Y\%m\%d).sql.gz

# 清理旧的Docker镜像
docker image prune -a -f --filter "until=720h"

# 查看磁盘使用
docker system df
```

### 性能监控

```bash
# 容器资源使用
docker stats

# 数据库连接数
docker-compose exec postgres psql -U vos_user -d vosadmin -c "SELECT count(*) FROM pg_stat_activity;"

# Redis内存使用
docker-compose exec redis redis-cli INFO memory
```

## 🔒 安全建议

1. **修改默认密码**
   - 修改 `.env` 中的数据库密码
   - 修改 SECRET_KEY

2. **限制端口访问**
   - 生产环境不要暴露数据库端口
   - 使用防火墙限制访问

3. **定期更新**
   - 定期拉取最新代码
   - 及时应用安全补丁

4. **备份策略**
   - 每天自动备份
   - 保留至少7天的备份
   - 定期测试恢复流程

## 📞 获取帮助

遇到问题时：

1. 查看日志：`docker-compose logs -f`
2. 检查服务状态：`bash deploy.sh` → 选择6
3. 查看迁移状态：`bash deploy.sh` → 选择5
4. 查看文档：`DATABASE_MIGRATION.md`

---

**提示**：生产环境部署前建议在测试环境充分验证！

