# 数据同步配置和初始化功能部署指南

## 📋 新功能概览

### 1. 客户管理页面增强
- **更新时间显示**: 显示数据最后同步时间
- **数据来源标识**: 标识数据来自实时API还是本地缓存

### 2. 数据同步配置管理
- **可视化配置**: 在"系统设置"中配置各类数据的同步频率
- **Cron表达式支持**: 使用标准Cron格式自定义同步周期
- **多类型支持**: 支持客户数据、话机状态、话单记录等不同类型的同步配置

### 3. VOS节点初始化同步
- **自动触发**: 新增VOS节点后自动开始数据同步
- **分阶段同步**:
  1. 首先同步所有客户数据
  2. 然后分批同步最近7天的历史话单
- **防超时机制**: 每天的话单分批请求，间隔30秒，避免单次请求过大

## 🚀 部署步骤

### 步骤1: 拉取最新代码

```bash
cd /data/yk-vos
git pull
```

### 步骤2: 运行数据库迁移

新版本添加了 `sync_configs` 表，需要运行迁移：

```bash
# 方式1: 自动迁移（推荐）
docker-compose restart backend

# 方式2: 手动迁移
docker-compose exec backend alembic upgrade head
```

### 步骤3: 重新构建并启动服务

```bash
# 重新构建前后端
docker-compose up -d --build backend frontend

# 查看日志确认启动成功
docker-compose logs -f backend frontend
```

### 步骤4: 验证新功能

1. **验证数据库迁移**:
   ```bash
   docker-compose exec postgres psql -U vos_user -d vosadmin -c "\d sync_configs"
   ```
   
   应该看到 `sync_configs` 表的结构。

2. **验证默认配置**:
   ```bash
   docker-compose exec postgres psql -U vos_user -d vosadmin -c "SELECT name, cron_expression, sync_type FROM sync_configs;"
   ```
   
   应该看到3条默认配置：
   - 客户数据同步 (*/10 * * * *)
   - 话机状态同步 (*/5 * * * *)
   - 话单数据同步 (30 1 * * *)

3. **验证前端功能**:
   - 访问 `http://your-server-ip:3000/settings`
   - 切换到"数据同步配置"标签
   - 应该能看到同步配置列表

## 📖 使用指南

### 1. 配置数据同步

1. 登录系统
2. 进入"系统设置" → "数据同步配置"
3. 点击"+ 添加配置"
4. 填写配置信息：
   - **配置名称**: 如"客户数据每5分钟同步"
   - **描述**: 可选的配置说明
   - **同步类型**: 选择要同步的数据类型
   - **Cron表达式**: 设置同步频率
   - **启用状态**: 是否启用此配置

#### Cron表达式示例

- `*/5 * * * *` - 每5分钟
- `*/10 * * * *` - 每10分钟
- `0 * * * *` - 每小时
- `0 2 * * *` - 每天凌晨2点
- `30 1 * * *` - 每天凌晨1:30
- `0 0 * * 0` - 每周日午夜

### 2. 新增VOS节点

1. 进入"系统设置" → "VOS 节点管理"
2. 点击"+ 添加节点"
3. 填写节点信息并保存
4. 系统会自动触发初始化同步：
   - ✅ 立即同步所有客户数据
   - ✅ 分7批同步最近7天的历史话单
   - ✅ 每批间隔30秒，防止API超时

5. 查看同步进度：
   ```bash
   # 查看Celery Worker日志
   docker-compose logs -f celery-worker
   ```

### 3. 查看同步时间

在"客户管理"页面，会显示：
- **当前VOS节点**: 显示当前查看的节点名称
- **最后同步时间**: 数据最后更新的时间
- **数据来源**: 实时数据或缓存数据

## ⚠️ 注意事项

### 关于Celery Beat动态调度

当前版本中，数据同步配置存储在数据库中，但 **Celery Beat的调度器尚未实现动态读取**。

这意味着：
- ✅ 可以在UI中创建和管理同步配置
- ✅ 配置会保存到数据库
- ❌ Celery Beat不会自动使用这些配置

**解决方案**（选择其一）：

#### 方案1: 手动更新Celery配置文件（临时）

修改 `backend/app/tasks/celery_app.py`:

```python
celery.conf.beat_schedule = {
    'sync-customers-custom': {
        'task': 'app.tasks.sync_tasks.sync_all_instances_customers',
        'schedule': crontab(minute='*/10'),  # 根据配置调整
    },
    # 添加其他配置...
}
```

然后重启Celery Beat:
```bash
docker-compose restart celery-beat
```

#### 方案2: 使用Database Scheduler（推荐，未来版本）

未来版本将集成 `celery-beat-scheduler` 或类似工具，实现完全动态调度。

#### 方案3: 定期重启Celery Beat

创建一个cron任务，定期重启Celery Beat以加载新配置（不推荐）。

### 关于首次同步

- 首次同步最近7天的话单可能需要较长时间（取决于数据量）
- 建议在业务低峰期添加VOS节点
- 可通过Celery日志监控同步进度

## 📊 监控和维护

### 查看同步任务状态

```bash
# 查看Celery Worker日志
docker-compose logs -f celery-worker

# 查看Celery Beat日志
docker-compose logs -f celery-beat

# 查看最近的同步记录
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
  SELECT account, synced_at, vos_instance_id 
  FROM customers 
  ORDER BY synced_at DESC 
  LIMIT 10;
"
```

### 数据库查询

```bash
# 查看同步配置
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
  SELECT id, name, sync_type, cron_expression, enabled 
  FROM sync_configs;
"

# 查看客户数据同步时间
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
  SELECT 
    vos_instance_id, 
    COUNT(*) as customer_count,
    MAX(synced_at) as last_sync
  FROM customers
  GROUP BY vos_instance_id;
"

# 查看话单数据统计
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
  SELECT 
    vos_id,
    DATE(start_time) as date,
    COUNT(*) as cdr_count
  FROM cdrs
  WHERE start_time >= NOW() - INTERVAL '7 days'
  GROUP BY vos_id, DATE(start_time)
  ORDER BY vos_id, date DESC;
"
```

## 🔧 故障排查

### 问题1: 同步配置不生效

**症状**: 在UI中创建了配置，但数据同步频率没有变化

**原因**: Celery Beat使用的是代码中定义的调度，不会自动读取数据库配置

**解决**:
1. 临时方案：手动修改 `backend/app/tasks/celery_app.py`
2. 长期方案：等待动态调度功能（未来版本）

### 问题2: 新增VOS节点后没有同步数据

**症状**: 添加节点后，客户管理页面显示为空

**检查步骤**:
1. 检查VOS节点状态是否为"启用"
2. 查看Celery Worker日志：
   ```bash
   docker-compose logs -f celery-worker | grep "初始化同步"
   ```
3. 检查VOS API是否可访问：
   ```bash
   curl -X POST http://vos-server/external/server/GetAllCustomers \
     -H "Content-Type: text/html;charset=UTF-8" \
     -d '{"type": 1}'
   ```

### 问题3: 话单同步超时

**症状**: Celery日志显示话单同步任务超时失败

**解决**:
1. 检查VOS API响应时间
2. 调整分批同步的间隔时间（修改 `initial_sync_tasks.py` 中的 `delay_seconds`）
3. 减少单次请求的日期范围

## 📝 回滚方案

如果新版本出现问题，可以回滚到之前的版本：

```bash
# 1. 回滚代码
git log --oneline -5  # 查看最近的提交
git reset --hard <previous-commit-hash>

# 2. 回滚数据库（如果需要）
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
  DROP TABLE IF EXISTS sync_configs;
"

# 3. 重新构建和启动
docker-compose down
docker-compose up -d --build
```

## ✅ 验证清单

部署完成后，请验证以下功能：

- [ ] 数据库迁移成功，`sync_configs` 表已创建
- [ ] 系统设置中可以看到"数据同步配置"标签
- [ ] 可以创建、编辑、删除同步配置
- [ ] 客户管理页面显示同步时间和数据来源
- [ ] 新增VOS节点后，Celery日志显示初始化同步开始
- [ ] 客户数据同步成功
- [ ] 历史话单分批同步成功

---

## 📞 技术支持

如有问题，请检查以下日志：

```bash
# Backend日志
docker-compose logs -f backend

# Celery Worker日志
docker-compose logs -f celery-worker

# Celery Beat日志
docker-compose logs -f celery-beat

# 数据库日志
docker-compose logs -f postgres
```

或参考 `README.md` 和 `UPGRADE_GUIDE.md` 获取更多信息。

