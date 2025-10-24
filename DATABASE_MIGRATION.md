# 数据库迁移指南

YK-VOS 项目使用 Alembic 进行数据库迁移管理，确保数据库结构的版本控制和安全升级。

## 🚀 自动迁移（推荐）

### 1. 使用部署脚本

```bash
bash deploy.sh
```

部署脚本提供以下选项：

- **选项1 - 快速更新**：拉取代码 → 执行迁移 → 重启服务
- **选项2 - 完整升级**：备份 → 拉取代码 → 重建镜像 → 迁移 → 重启
- **选项4 - 单独执行迁移**：仅执行数据库迁移
- **选项5 - 查看迁移状态**：查看当前迁移版本和历史

### 2. 容器启动时自动迁移

后端容器启动时会自动执行 `alembic upgrade head`，无需手动操作。

查看启动日志：
```bash
docker-compose logs backend | grep -i migration
```

## 📝 手动迁移操作

### 查看当前迁移版本

```bash
docker-compose exec backend alembic current
```

### 查看迁移历史

```bash
docker-compose exec backend alembic history --verbose
```

### 升级到最新版本

```bash
docker-compose exec backend alembic upgrade head
```

### 升级到指定版本

```bash
docker-compose exec backend alembic upgrade <revision_id>
```

例如：
```bash
docker-compose exec backend alembic upgrade 0010
```

### 回滚一个版本

```bash
docker-compose exec backend alembic downgrade -1
```

### 回滚到指定版本

```bash
docker-compose exec backend alembic downgrade <revision_id>
```

### 回滚到初始状态（危险！）

```bash
docker-compose exec backend alembic downgrade base
```

## 🛠️ 创建新的迁移

### 自动生成迁移（检测模型变化）

```bash
docker-compose exec backend alembic revision --autogenerate -m "描述你的修改"
```

### 手动创建迁移

```bash
docker-compose exec backend alembic revision -m "描述你的修改"
```

生成的迁移文件位于：`backend/app/alembic/versions/`

### 编辑迁移文件

1. 在 `backend/app/alembic/versions/` 目录找到新生成的文件
2. 编辑 `upgrade()` 函数（升级操作）
3. 编辑 `downgrade()` 函数（回滚操作）
4. 保存并测试

## 💾 数据库备份与恢复

### 备份数据库

```bash
# 备份完整数据库
docker exec yk_vos_timescaledb pg_dump -U vos_user -d vosadmin > backup_$(date +%Y%m%d_%H%M%S).sql

# 仅备份数据（不含表结构）
docker exec yk_vos_timescaledb pg_dump -U vos_user -d vosadmin --data-only > backup_data.sql

# 仅备份表结构
docker exec yk_vos_timescaledb pg_dump -U vos_user -d vosadmin --schema-only > backup_schema.sql
```

### 恢复数据库

```bash
# 恢复完整备份
cat backup_20251024_120000.sql | docker exec -i yk_vos_timescaledb psql -U vos_user -d vosadmin

# 恢复前先删除现有数据（危险！）
docker exec yk_vos_timescaledb psql -U vos_user -d vosadmin -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
cat backup.sql | docker exec -i yk_vos_timescaledb psql -U vos_user -d vosadmin
```

## 🔍 迁移故障排查

### 迁移失败怎么办？

1. **查看错误日志**
   ```bash
   docker-compose logs backend | tail -n 50
   ```

2. **检查数据库连接**
   ```bash
   docker-compose exec postgres pg_isready -U vos_user -d vosadmin
   ```

3. **查看当前迁移状态**
   ```bash
   docker-compose exec backend alembic current
   docker-compose exec backend alembic history
   ```

4. **手动检查数据库表**
   ```bash
   docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dt"
   ```

### 常见问题

#### 问题1：迁移被标记但未实际执行

**解决方法：**
```bash
# 回滚到上一个版本
docker-compose exec backend alembic downgrade -1

# 重新执行迁移
docker-compose exec backend alembic upgrade head
```

#### 问题2：迁移冲突

**解决方法：**
```bash
# 查看冲突的迁移
docker-compose exec backend alembic branches

# 合并分支（如果有多个头）
docker-compose exec backend alembic merge heads -m "merge branches"

# 执行合并后的迁移
docker-compose exec backend alembic upgrade head
```

#### 问题3：表已存在错误

**解决方法：**
```bash
# 标记迁移为已执行（不实际运行SQL）
docker-compose exec backend alembic stamp head

# 或者删除冲突的表后重新迁移
docker-compose exec postgres psql -U vos_user -d vosadmin -c "DROP TABLE IF EXISTS table_name CASCADE;"
docker-compose exec backend alembic upgrade head
```

## 📋 迁移版本历史

当前迁移版本列表：

- `0001` - 初始化基础表结构
- `0002` - 添加CDR（话单）表
- `0003` - 添加CDR哈希索引
- `0004` - 添加VOS数据缓存表
- `0005` - 添加增强版话机和网关模型
- `0006` - 优化CDR索引
- `0007` - 添加客户表
- `0008` - 添加同步配置表
- `0009` - 迁移到TimescaleDB（CDR超表）
- `0010` - 添加VOS健康检查表 ⭐ 最新

## 🔒 安全建议

1. **生产环境迁移前必须备份**
   ```bash
   bash deploy.sh  # 选择"完整升级"会自动备份
   ```

2. **在测试环境先验证迁移**
   ```bash
   # 在测试环境执行
   docker-compose exec backend alembic upgrade head
   ```

3. **准备回滚方案**
   - 保存备份文件
   - 记录当前版本号
   - 准备回滚命令

4. **迁移失败后的应急操作**
   ```bash
   # 1. 停止服务
   docker-compose stop backend celery-worker celery-beat
   
   # 2. 恢复备份
   cat backup_latest.sql | docker exec -i yk_vos_timescaledb psql -U vos_user -d vosadmin
   
   # 3. 重启服务
   docker-compose up -d
   ```

## 💡 最佳实践

1. **定期备份**：每天自动备份数据库
2. **测试先行**：新迁移先在测试环境验证
3. **版本控制**：迁移文件纳入 Git 管理
4. **文档更新**：重要迁移要更新文档
5. **监控日志**：迁移后检查应用日志

## 📞 获取帮助

如遇到问题，请：

1. 查看后端日志：`docker-compose logs -f backend`
2. 查看数据库日志：`docker-compose logs -f postgres`
3. 检查迁移历史：`docker-compose exec backend alembic history`
4. 查看详细错误：`docker-compose exec backend alembic upgrade head --verbose`

---

**注意**：所有生产环境的迁移操作都应在维护窗口期进行，并提前通知用户。

