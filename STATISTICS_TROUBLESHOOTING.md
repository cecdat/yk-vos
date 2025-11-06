# 统计数据任务排查指南

## 问题：统计数据页面没有数据显示

### 检查步骤

#### 1. 检查 Celery Beat 是否正常运行

```bash
# 查看 Celery Beat 容器日志
docker logs yk_vos_celery_beat

# 应该看到类似这样的日志：
# celery beat v5.x.x is starting.
# DatabaseScheduler: Schedule changed.
```

#### 2. 检查统计任务是否被调度

在 Celery Beat 日志中查找：
```
calculate-cdr-statistics-daily
```

应该看到任务在每天凌晨 2:30 被调度。

#### 3. 检查 Celery Worker 是否执行了任务

```bash
# 查看 Celery Worker 日志
docker logs yk_vos_celery_worker

# 应该看到类似这样的日志：
# [INFO] Task app.tasks.cdr_statistics_tasks.calculate_all_instances_statistics[...] received
# ================================================================================
# 📊 开始执行统计任务: calculate_all_instances_statistics
# ================================================================================
```

#### 4. 检查数据库迁移是否执行

```bash
# 进入后端容器
docker exec -it yk_vos_backend bash

# 检查迁移状态
alembic current

# 应该看到最新的迁移版本：0016_gateway_type

# 如果没有，执行迁移
alembic upgrade head
```

#### 5. 检查 VOS 实例配置

确保：
- VOS 实例已启用（`enabled = True`）
- VOS 实例有 UUID（`vos_uuid` 不为空）

```sql
-- 在 PostgreSQL 中检查
SELECT id, name, enabled, vos_uuid FROM vos_instances;
```

#### 6. 检查 ClickHouse 中是否有话单数据

```sql
-- 在 ClickHouse 中检查
SELECT count() as total FROM vos_cdrs.cdrs;

-- 检查特定 VOS 实例的数据
SELECT count() as total 
FROM vos_cdrs.cdrs 
WHERE vos_id = 1 
  AND toDate(start) >= today() - 7;
```

#### 7. 检查统计表是否有数据

```sql
-- 在 PostgreSQL 中检查
SELECT count() FROM vos_cdr_statistics;
SELECT count() FROM account_cdr_statistics;
SELECT count() FROM gateway_cdr_statistics;

-- 检查最近的统计数据
SELECT * FROM vos_cdr_statistics 
ORDER BY statistic_date DESC 
LIMIT 10;
```

#### 8. 手动触发统计任务

如果自动任务没有执行，可以手动触发：

```bash
# 通过 API 触发
curl -X POST "http://localhost:3001/api/v1/vos/instances/1/statistics/calculate" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 或者在 Python 中
from app.tasks.cdr_statistics_tasks import calculate_all_instances_statistics
calculate_all_instances_statistics.delay()
```

#### 9. 检查日志中的错误信息

查看 Celery Worker 日志中的错误：

```bash
docker logs yk_vos_celery_worker 2>&1 | grep -i "error\|exception\|失败"
```

常见错误：
- `relation "gateway_cdr_statistics" does not exist` - 需要执行数据库迁移
- `VOS实例没有UUID` - 需要为 VOS 实例设置 UUID
- `ClickHouse中没有找到话单数据` - 需要先同步话单数据

#### 10. 检查任务执行时间

统计任务在每天凌晨 2:30 执行。如果系统时间不正确，任务可能不会在预期时间执行。

```bash
# 检查系统时间
date

# 检查时区设置
timedatectl
```

### 常见问题解决

#### 问题1：任务没有执行

**原因**：Celery Beat 没有运行或任务没有正确注册

**解决**：
1. 检查 `celery_app.py` 中的任务配置
2. 重启 Celery Beat 容器
3. 检查任务是否被正确导入

#### 问题2：任务执行但统计数据为空

**原因**：
1. ClickHouse 中没有话单数据
2. 日期范围不正确
3. VOS UUID 不匹配

**解决**：
1. 检查 ClickHouse 中是否有数据
2. 检查 VOS 实例的 UUID 是否正确
3. 检查话单同步任务是否正常运行

#### 问题3：数据库表不存在

**原因**：数据库迁移没有执行

**解决**：
```bash
docker exec -it yk_vos_backend alembic upgrade head
```

#### 问题4：网关统计表结构错误

**原因**：迁移 `0016_gateway_type` 没有执行

**解决**：
```bash
docker exec -it yk_vos_backend alembic upgrade head
```

### 调试命令

```bash
# 查看所有 Celery 任务
docker exec -it yk_vos_celery_worker celery -A app.tasks.celery_app inspect active

# 查看任务注册情况
docker exec -it yk_vos_celery_worker celery -A app.tasks.celery_app inspect registered

# 查看 Celery Beat 调度
docker exec -it yk_vos_celery_beat celery -A app.tasks.celery_app beat --loglevel=info
```

### 日志关键字

在日志中查找以下关键字来诊断问题：

- `📊 开始执行统计任务` - 任务开始执行
- `查询到 X 个启用的VOS实例` - 找到的实例数量
- `⚠️ 没有启用的VOS实例` - 没有找到实例
- `⚠️ VOS实例没有UUID` - 实例缺少 UUID
- `✅ 已创建统计任务` - 任务创建成功
- `❌ 统计失败` - 任务执行失败
- `ClickHouse中最近7天的话单数量` - 检查数据量
- `⚠️ ClickHouse中没有找到话单数据` - 没有数据

