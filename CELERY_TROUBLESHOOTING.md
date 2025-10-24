# Celery任务执行问题排查指南

## 问题现象

- ✅ 手动执行测试脚本能成功写入数据
- ❌ 前端触发同步显示"成功"，但没有实际写入数据
- ❌ 没有显示同步了多少条数据

## 原因分析

这说明：
1. 代码逻辑正常（测试脚本能成功）
2. ClickHouse连接正常
3. **问题出在Celery异步任务执行上**

---

## 快速排查步骤

### 步骤1：检查Celery Worker是否运行

```bash
docker ps | grep celery
```

**预期输出**：
```
yk_vos_celery_worker    Up 2 hours
yk_vos_celery_beat      Up 2 hours
```

**如果看不到或状态是 `Exit`**：
```bash
# 查看错误日志
docker logs yk_vos_celery_worker --tail 50

# 重启服务
docker-compose restart celery-worker celery-beat
```

---

### 步骤2：查看Celery Worker实时日志

**打开一个新终端，实时监控日志**：
```bash
docker logs yk_vos_celery_worker -f
```

保持这个终端开着，然后在前端触发同步，观察日志输出。

**正常情况应该看到**：
```
[2025-10-24 10:30:00] Received task: app.tasks.manual_sync_tasks.sync_single_customer_cdrs
[2025-10-24 10:30:00] Task app.tasks.manual_sync_tasks.sync_single_customer_cdrs[xxx] succeeded
```

**如果没有任何日志输出**：说明任务根本没到达Worker！

---

### 步骤3：检查任务是否注册

```bash
docker exec -it yk_vos_celery_worker celery -A app.tasks.celery_app inspect registered
```

**应该能看到这些任务**：
```
app.tasks.manual_sync_tasks.sync_single_customer_cdrs
app.tasks.sync_tasks.sync_all_instances_cdrs
app.tasks.sync_tasks.sync_customers_for_instance
app.tasks.initial_sync_tasks.sync_cdrs_for_single_day
```

**如果看不到 `sync_single_customer_cdrs`**：说明任务模块没有正确导入！

---

### 步骤4：检查Redis连接

```bash
# 测试Redis连接
docker exec -it yk_vos_redis redis-cli ping
# 应该返回：PONG

# 查看任务队列长度
docker exec -it yk_vos_redis redis-cli llen celery
# 应该返回数字（通常是0）

# 查看所有键
docker exec -it yk_vos_redis redis-cli keys "*"
```

---

### 步骤5：手动触发任务测试

进入Backend容器，手动触发一个任务：

```bash
docker exec -it yk_vos_backend bash

# 进入Python Shell
python

# 手动触发任务
from app.tasks.manual_sync_tasks import sync_single_customer_cdrs
from app.core.db import SessionLocal
from app.models.customer import Customer
from app.models.vos_instance import VOSInstance

db = SessionLocal()

# 获取一个客户
inst = db.query(VOSInstance).first()
customer = db.query(Customer).filter(Customer.vos_instance_id == inst.id).first()

# 触发任务
result = sync_single_customer_cdrs.apply_async(
    args=[inst.id, customer.id, 1]
)

print(f"任务ID: {result.id}")
print(f"任务状态: {result.status}")

# 等待几秒后检查状态
import time
time.sleep(5)
print(f"任务状态: {result.status}")
print(f"任务结果: {result.result}")

exit()
exit
```

---

## 常见问题及解决方案

### 问题1：Celery Worker 持续重启或崩溃

**症状**：`docker ps` 显示 celery-worker 不断重启

**查看日志**：
```bash
docker logs yk_vos_celery_worker --tail 100
```

**常见错误**：
- `ModuleNotFoundError`: 缺少Python包
- `ImportError`: 导入错误
- `Connection refused`: Redis或数据库连接失败

**解决方案**：
```bash
# 重新构建镜像
docker-compose down
docker-compose build celery-worker
docker-compose up -d
```

---

### 问题2：任务没有注册

**症状**：`inspect registered` 看不到你的任务

**原因**：
- 任务模块没有被 `celery_app.py` 导入
- 模块路径错误

**检查文件**：`backend/app/tasks/celery_app.py`

```python
# 确保包含这些导入
celery.autodiscover_tasks([
    'app.tasks.sync_tasks',
    'app.tasks.initial_sync_tasks',
    'app.tasks.manual_sync_tasks',  # ← 必须有这个！
    'app.tasks.health_tasks'
])
```

**修复后重启**：
```bash
docker-compose restart celery-worker
```

---

### 问题3：任务发送但不执行

**症状**：
- Backend日志显示 "任务已启动，任务ID: xxx"
- Celery Worker 日志没有任何输出
- Redis队列有积压

**可能原因**：
1. Celery Worker 和 Backend 使用不同的 Redis 配置
2. 队列名称不匹配
3. Worker 没有监听正确的队列

**解决方案**：

检查环境变量配置：
```bash
# Backend的Redis URL
docker exec -it yk_vos_backend env | grep REDIS

# Celery Worker的Redis URL
docker exec -it yk_vos_celery_worker env | grep REDIS
```

**必须完全一致！**

如果不一致，修改 `docker-compose.yaml`：
```yaml
backend:
  environment:
    REDIS_URL: redis://redis:6379/0

celery-worker:
  environment:
    REDIS_URL: redis://redis:6379/0  # ← 必须一致
```

---

### 问题4：任务执行了但没有结果

**症状**：
- Celery日志显示任务已接收
- 但没有看到 "succeeded" 或错误信息
- ClickHouse中没有数据

**可能原因**：任务执行过程中出错，但错误没有被正确记录

**解决方案**：

修改日志级别为DEBUG：
```bash
docker-compose down

# 编辑 docker-compose.yaml
# 找到 celery-worker 部分，添加：
celery-worker:
  command: celery -A app.tasks.celery_app worker --loglevel=debug

docker-compose up -d
```

然后查看详细日志：
```bash
docker logs yk_vos_celery_worker -f
```

---

## 完整诊断流程

### 在服务器上执行：

```bash
cd /data/yk-vos

# 1. 更新代码
git pull origin main

# 2. 停止所有服务
docker-compose down

# 3. 清理旧容器（可选）
docker system prune -f

# 4. 重新构建并启动
docker-compose build
docker-compose up -d

# 5. 等待服务就绪
sleep 30

# 6. 检查服务状态
docker-compose ps

# 7. 查看 Celery Worker 启动日志
docker logs yk_vos_celery_worker --tail 50

# 8. 检查任务注册
docker exec -it yk_vos_celery_worker celery -A app.tasks.celery_app inspect registered

# 9. 开始实时监控
docker logs yk_vos_celery_worker -f
```

**在另一个终端**：
```bash
# 监控Backend日志
docker logs yk_vos_backend -f
```

**然后在前端触发同步**，观察两个日志窗口的输出。

---

## 预期的正常日志流程

### Backend日志（yk_vos_backend）：
```
INFO: 用户 admin 触发节点 1 客户 云客测试 话单同步
INFO: 任务ID: abc123...
```

### Celery Worker日志（yk_vos_celery_worker）：
```
[2025-10-24 10:30:00,123: INFO/MainProcess] Received task: app.tasks.manual_sync_tasks.sync_single_customer_cdrs[abc123...]
[2025-10-24 10:30:00,456: INFO/ForkPoolWorker-1] 📞 开始同步单个客户话单: 19-vos - 云客测试 (最近1天)
[2025-10-24 10:30:02,789: INFO/ForkPoolWorker-1] ✅ 客户 云客测试: 同步 28 条话单
[2025-10-24 10:30:02,890: INFO/MainProcess] Task app.tasks.manual_sync_tasks.sync_single_customer_cdrs[abc123...] succeeded in 2.5s
```

---

## 如果以上都正常，但还是没有数据

### 最后的检查：

1. **确认ClickHouse中真的没有数据**：
```bash
docker exec -it yk_vos_clickhouse clickhouse-client
SELECT count() FROM vos_cdrs.cdrs;
SELECT count() FROM vos_cdrs.cdrs WHERE vos_id = 1;  -- 替换为你的VOS ID
exit;
```

2. **检查是否有重复数据保护**：
由于ID是基于`flow_no`生成的，相同的话单不会重复插入。

清空数据重新测试：
```bash
docker exec -it yk_vos_clickhouse clickhouse-client
TRUNCATE TABLE vos_cdrs.cdrs;
exit;
```

3. **手动执行一次测试**：
```bash
docker exec -it yk_vos_backend python test_clickhouse_sync.py
```

如果测试成功，再通过前端触发。

---

## 需要提供的调试信息

如果问题仍未解决，请提供：

1. **服务状态**：
```bash
docker-compose ps > service_status.txt
```

2. **Celery Worker日志**：
```bash
docker logs yk_vos_celery_worker --tail 200 > celery_worker.log
```

3. **Backend日志**：
```bash
docker logs yk_vos_backend --tail 200 > backend.log
```

4. **任务注册信息**：
```bash
docker exec -it yk_vos_celery_worker celery -A app.tasks.celery_app inspect registered > registered_tasks.txt
```

5. **环境变量**：
```bash
docker exec -it yk_vos_backend env | grep -E "REDIS|CELERY" > backend_env.txt
docker exec -it yk_vos_celery_worker env | grep -E "REDIS|CELERY" > celery_env.txt
```

将这些文件发送给技术支持。

