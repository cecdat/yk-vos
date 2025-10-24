# 同步功能故障排查指南

## 问题：手动触发同步后没有数据进入ClickHouse

### 排查步骤

#### 1. 检查服务是否正常运行

```bash
cd /opt/yk-vos
docker-compose ps
```

确认以下服务都是 `Up` 状态：
- `yk_vos_backend`
- `yk_vos_celery_worker` ⚠️ 重要：负责执行同步任务
- `yk_vos_celery_beat`
- `yk_vos_clickhouse`
- `yk_vos_redis`

如果 `celery_worker` 不是 `Up` 状态，重启它：
```bash
docker-compose restart celery-worker
```

---

#### 2. 运行诊断脚本

```bash
docker exec -it yk_vos_backend python test_clickhouse_sync.py
```

这个脚本会自动测试：
1. ✅ ClickHouse 连接
2. ✅ ClickHouse 中的数据量
3. ✅ VOS API 调用
4. ✅ 手动同步流程

**预期输出示例**：
```
🔍 ClickHouse 同步功能测试
============================================================
1. 测试 ClickHouse 连接
============================================================
✅ ClickHouse 连接成功！
   版本: 24.3.1.1
   cdrs 表记录数: 0

============================================================
2. 测试 VOS API 调用
============================================================
📍 VOS实例: 19楼-VOS
   地址: http://xxx:62020
   客户数: 5
   测试查询客户: 百融消金
   ✅ API调用成功，返回 123 条话单

============================================================
3. 测试手动同步到 ClickHouse
============================================================
📍 同步测试
   VOS实例: 19楼-VOS
   客户: 百融消金
   从VOS获取到 123 条话单
   正在写入 ClickHouse...
   ✅ 成功写入 123 条话单
   📊 ClickHouse中该VOS实例的话单总数: 123

============================================================
✅ 所有测试通过！
============================================================
```

---

#### 3. 查看 Celery Worker 日志

```bash
# 查看最近50条日志
docker logs yk_vos_celery_worker --tail 50

# 实时查看日志
docker logs yk_vos_celery_worker -f
```

**关键日志标识**：
- `[2025-10-24 xx:xx:xx,xxx: INFO/ForkPoolWorker-1] 🚀 开始同步...` - 任务开始
- `[2025-10-24 xx:xx:xx,xxx: INFO/ForkPoolWorker-1] ✅ ...同步完成: X 条` - 任务成功
- `[2025-10-24 xx:xx:xx,xxx: ERROR/ForkPoolWorker-1] ❌ ...失败` - 任务失败

**常见错误**：
- `Connection refused` - Redis或ClickHouse未启动
- `relation "vos_instances" does not exist` - 数据库未初始化
- `No module named 'xxx'` - 依赖包未安装

---

#### 4. 检查 ClickHouse 数据

```bash
# 进入ClickHouse容器
docker exec -it yk_vos_clickhouse clickhouse-client

# 查询话单总数
SELECT count() FROM vos_cdrs.cdrs;

# 按VOS实例分组统计
SELECT vos_id, count() as count 
FROM vos_cdrs.cdrs 
GROUP BY vos_id;

# 查看最近的话单
SELECT 
    vos_id,
    caller_e164,
    callee_e164,
    begin_time,
    created_at
FROM vos_cdrs.cdrs
ORDER BY created_at DESC
LIMIT 10;

# 退出
exit;
```

---

#### 5. 手动触发同步测试

在前端执行手动同步后，立即查看日志：

```bash
# Terminal 1: 实时查看 backend 日志
docker logs yk_vos_backend -f

# Terminal 2: 实时查看 celery_worker 日志
docker logs yk_vos_celery_worker -f
```

**正常流程**：
1. Backend 日志：`用户 admin 触发...话单同步，任务ID: xxx`
2. Celery Worker 日志：`Received task: app.tasks.xxx`
3. Celery Worker 日志：`开始同步...`
4. Celery Worker 日志：`✅ ...同步完成: X 条`

---

#### 6. 检查Redis连接

```bash
# 进入 backend 容器
docker exec -it yk_vos_backend bash

# 测试 Redis 连接
python -c "
import redis
from app.core.config import settings
r = redis.from_url(settings.REDIS_URL)
print('Redis连接成功')
print('Ping:', r.ping())
"

# 退出
exit
```

---

#### 7. 检查VOS节点配置

进入前端系统：
1. 登录系统
2. 进入"系统设置" → "VOS节点管理"
3. 确认：
   - ✅ 至少有一个节点
   - ✅ 节点状态为"启用中"
   - ✅ VOS地址正确（能访问）
   - ✅ 健康状态为"健康"

如果健康状态为"异常"：
- 检查VOS服务器是否在线
- 检查网络连接
- 检查防火墙设置

---

#### 8. 检查客户数据

```bash
# 进入 backend 容器
docker exec -it yk_vos_backend bash

# 进入 Python Shell
python

# 检查客户数据
from app.core.db import SessionLocal
from app.models.customer import Customer
from app.models.vos_instance import VOSInstance

db = SessionLocal()

# 查看VOS实例
instances = db.query(VOSInstance).all()
for inst in instances:
    print(f"实例: {inst.name} (ID={inst.id}, 启用={inst.enabled})")

# 查看客户
customers = db.query(Customer).all()
print(f"客户总数: {len(customers)}")
for c in customers[:5]:
    print(f"  - {c.account} (VOS#{c.vos_instance_id})")

db.close()
exit()

# 退出容器
exit
```

---

## 常见问题解决方案

### 问题1：Celery Worker 无法启动

**症状**：`docker-compose ps` 显示 `celery-worker` 状态为 `Exit`

**解决方案**：
```bash
# 查看错误日志
docker logs yk_vos_celery_worker

# 重新构建并启动
docker-compose down
docker-compose up -d --build celery-worker
```

---

### 问题2：ClickHouse 无数据但日志显示成功

**可能原因**：
- ClickHouse表结构不匹配
- 数据插入失败但未抛出异常

**解决方案**：
```bash
# 1. 检查ClickHouse表结构
docker exec -it yk_vos_clickhouse clickhouse-client
SHOW CREATE TABLE vos_cdrs.cdrs;

# 2. 手动测试插入
INSERT INTO vos_cdrs.cdrs (vos_id, caller_e164, callee_e164, begin_time) 
VALUES (1, '13800000000', '10086', '2025-10-24 10:00:00');

# 3. 查询验证
SELECT * FROM vos_cdrs.cdrs LIMIT 1;
```

---

### 问题3：VOS API 调用失败

**症状**：日志显示 `VOS API调用失败` 或 `retCode != 0`

**解决方案**：
1. 检查VOS服务器是否在线
2. 检查VOS API地址是否正确
3. 手动测试API调用：
```bash
curl -X POST http://VOS地址:62020/external/server/GetCdr \
  -H "Content-Type: application/json" \
  -d '{
    "accounts": [],
    "beginTime": "20251023",
    "endTime": "20251024"
  }'
```

---

### 问题4：Redis 连接失败

**症状**：日志显示 `连接 Redis 失败`

**解决方案**：
```bash
# 1. 检查Redis是否启动
docker ps | grep redis

# 2. 重启Redis
docker-compose restart redis

# 3. 检查Redis配置
docker exec -it yk_vos_redis redis-cli
PING  # 应该返回 PONG
exit
```

---

### 问题5：没有客户数据

**症状**：同步时提示"没有客户数据"

**解决方案**：
1. 先同步客户数据：
   - 进入"同步管理" → "客户数据同步"
   - 选择对应的VOS节点
   - 点击"立即同步客户数据"

2. 等待客户同步完成后，再同步话单

---

## 完整重置步骤（最后手段）

如果以上方法都无效，执行完整重置：

```bash
cd /opt/yk-vos

# 1. 停止所有服务
docker-compose down

# 2. 清理旧数据（可选，会删除所有数据）
# rm -rf data/clickhouse/*
# rm -rf data/postgres/*

# 3. 重新启动
docker-compose up -d

# 4. 等待所有服务就绪（约30秒）
sleep 30

# 5. 检查服务状态
docker-compose ps

# 6. 添加VOS节点（通过前端）

# 7. 同步客户数据

# 8. 同步话单数据

# 9. 运行诊断
docker exec -it yk_vos_backend python test_clickhouse_sync.py
```

---

## 联系支持

如果问题仍未解决，请提供以下信息：

1. 诊断脚本输出：
```bash
docker exec -it yk_vos_backend python test_clickhouse_sync.py > debug.log 2>&1
```

2. 服务状态：
```bash
docker-compose ps > services.log
```

3. 最近的日志：
```bash
docker logs yk_vos_backend --tail 100 > backend.log 2>&1
docker logs yk_vos_celery_worker --tail 100 > celery.log 2>&1
docker logs yk_vos_clickhouse --tail 100 > clickhouse.log 2>&1
```

将这些文件发送给技术支持。

