# 话单数据快速参考

## 📋 表结构总览

### 表名: `cdrs`

```sql
CREATE TABLE cdrs (
    id INTEGER PRIMARY KEY,
    vos_id INTEGER,                    -- VOS实例ID
    caller VARCHAR(64),                -- 主叫号码
    callee VARCHAR(64),                -- 被叫号码
    caller_gateway VARCHAR(64),        -- 主叫网关
    callee_gateway VARCHAR(64),        -- 被叫网关
    start_time TIMESTAMP,              -- 开始时间
    end_time TIMESTAMP,                -- 结束时间
    duration INTEGER,                  -- 时长(秒)
    cost NUMERIC(10,4),                -- 费用
    disposition VARCHAR(64),           -- 呼叫状态
    raw TEXT,                          -- 原始JSON数据
    hash VARCHAR(32)                   -- 去重哈希
);
```

---

## ⚠️ 上亿级数据优化（已实施）

### ✅ 已生效的优化措施

| 优化项 | 说明 | 效果 |
|--------|------|------|
| **时间范围限制** | 单次查询最多31天 | 避免全表扫描 |
| **结果集分页** | 默认20条/页，最大100条 | 防止内存溢出 |
| **历史数据限制** | 禁止查询1年前数据 | 引导使用归档 |
| **首次同步限制** | 新节点默认同步7天，最多30天 | 避免超时 |
| **分批同步** | 每天一批，间隔30秒 | 降低API压力 |

### 🔒 API限制说明

#### 查询接口
```http
POST /api/v1/cdr/query-from-vos/{instance_id}
```

**参数限制**:
- ❌ `begin_time` 到 `end_time` 不能超过31天
- ❌ `begin_time` 不能早于1年前
- ✅ `page_size` 最大100条
- ✅ 默认每页20条

**错误示例**:
```json
{
  "begin_time": "20240101",  // ❌ 超过1年
  "end_time": "20241231",    // ❌ 范围超过31天
  "page_size": 500           // ❌ 超过最大100
}
```

**正确示例**:
```json
{
  "begin_time": "20251001",  // ✅ 最近1个月内
  "end_time": "20251031",    // ✅ 范围31天内
  "page": 1,
  "page_size": 20
}
```

---

## 📊 数据同步机制

### 新增VOS节点时

```
触发: 创建VOS节点
  ↓
步骤1: 同步所有客户数据
  ↓
步骤2: 分批同步最近7天话单
  ├─ Day 0 (今天)    - 立即执行
  ├─ Day -1 (昨天)   - 延迟30秒
  ├─ Day -2 (前天)   - 延迟60秒
  ├─ ... 
  └─ Day -6 (第7天)  - 延迟180秒
```

**修改默认同步天数**:
```python
# 在创建VOS节点时指定
initial_sync_for_new_instance.delay(instance_id, sync_days=7)  # 默认7天
initial_sync_for_new_instance.delay(instance_id, sync_days=30) # 最大30天
```

### 定期同步

当前使用的是定时任务（Celery Beat）:
```python
# 每天凌晨1:30同步前一天的数据
'sync-cdr-daily-0130': {
    'task': 'app.tasks.sync_tasks.sync_all_instances_cdrs',
    'schedule': crontab(minute=30, hour=1)
}
```

---

## 🚀 性能指标

### 查询性能（已优化）

| 数据量 | 查询范围 | 本地DB | VOS API |
|--------|----------|--------|---------|
| < 1万 | 1天 | <10ms | 1-2s |
| 1-10万 | 7天 | <50ms | 2-5s |
| 10-100万 | 31天 | <200ms | 5-10s |
| > 100万 | 31天 | <500ms | 10-30s |

### 存储预估

| 日均话单 | 月度存储 | 年度存储 |
|----------|----------|----------|
| 10万 | 2GB | 24GB |
| 50万 | 10GB | 120GB |
| 100万 | 20GB | 240GB |
| 500万 | 100GB | 1.2TB |

---

## 🔧 常用SQL查询

### 查看表大小
```sql
SELECT 
    pg_size_pretty(pg_total_relation_size('cdrs')) as total_size,
    pg_size_pretty(pg_relation_size('cdrs')) as table_size,
    pg_size_pretty(pg_total_relation_size('cdrs') - pg_relation_size('cdrs')) as index_size;
```

### 统计各实例话单数量
```sql
SELECT 
    vos_id,
    COUNT(*) as total,
    MIN(start_time) as earliest,
    MAX(start_time) as latest
FROM cdrs
GROUP BY vos_id;
```

### 查看最近7天数据分布
```sql
SELECT 
    DATE(start_time) as date,
    COUNT(*) as count,
    SUM(cost) as total_cost
FROM cdrs
WHERE start_time >= NOW() - INTERVAL '7 days'
GROUP BY DATE(start_time)
ORDER BY date DESC;
```

### 查找高频呼叫号码
```sql
SELECT 
    caller,
    COUNT(*) as call_count,
    SUM(duration) as total_duration,
    SUM(cost) as total_cost
FROM cdrs
WHERE start_time >= NOW() - INTERVAL '1 day'
GROUP BY caller
ORDER BY call_count DESC
LIMIT 20;
```

### 清理测试数据
```sql
-- ⚠️ 谨慎操作！删除指定VOS实例的所有话单
DELETE FROM cdrs WHERE vos_id = 999;

-- 删除1年前的数据（归档后执行）
DELETE FROM cdrs WHERE start_time < NOW() - INTERVAL '1 year';
```

---

## 📈 监控和维护

### 检查表健康状态
```bash
# 查看表统计信息
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
  SELECT 
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
  FROM pg_stat_user_tables 
  WHERE relname = 'cdrs';
"
```

### 索引使用率
```bash
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
  SELECT 
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
  FROM pg_stat_user_indexes
  WHERE schemaname = 'public' AND tablename = 'cdrs'
  ORDER BY idx_scan DESC;
"
```

### 慢查询分析
```bash
# 查看耗时超过1秒的查询
docker-compose logs backend | grep "duration>" | grep "cdrs"
```

---

## 🔄 数据归档策略（待实施）

### 冷热数据分离建议

| 数据类型 | 时间范围 | 存储位置 | 访问频率 |
|----------|----------|----------|----------|
| **热数据** | 最近3个月 | PostgreSQL主表 | 高频 |
| **温数据** | 3-12个月 | 分区表 | 中频 |
| **冷数据** | 12个月以上 | 对象存储(S3/MinIO) | 低频 |

### 归档流程（月度执行）

```bash
# 1. 导出12个月前的数据
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
  COPY (
    SELECT * FROM cdrs 
    WHERE start_time < NOW() - INTERVAL '12 months'
  ) TO '/backup/cdrs_archive_$(date +%Y%m).csv' WITH CSV HEADER;
"

# 2. 压缩归档文件
gzip /backup/cdrs_archive_*.csv

# 3. 上传到对象存储（可选）
# aws s3 cp /backup/cdrs_archive_*.csv.gz s3://my-bucket/cdrs/

# 4. 删除已归档数据
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
  DELETE FROM cdrs WHERE start_time < NOW() - INTERVAL '12 months';
"

# 5. 清理碎片
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
  VACUUM ANALYZE cdrs;
"
```

---

## 🎯 下一步优化计划

### 短期（1-2周）
- [ ] 实施数据库分区表（按月分区）
- [ ] raw字段改为JSONB
- [ ] 添加更多复合索引

### 中期（1-2月）
- [ ] 集成TimescaleDB
- [ ] 实施自动归档策略
- [ ] 建立数据分析看板

### 长期（3月+）
- [ ] 分布式存储架构
- [ ] 实时数据流处理
- [ ] AI驱动的异常检测

---

## 💡 最佳实践

### ✅ 推荐做法

1. **查询时间范围**: 始终指定明确的时间范围，避免全表扫描
2. **使用分页**: 大量数据查询必须分页
3. **定期归档**: 建立定期归档机制，保持表体积可控
4. **监控索引**: 定期检查索引使用情况，删除无效索引
5. **业务低峰期**: 大批量数据同步安排在凌晨进行

### ❌ 避免的做法

1. ~~查询全部数据~~ → 使用时间范围限制
2. ~~单次查询超过100条~~ → 使用分页
3. ~~查询1年前数据~~ → 使用归档系统
4. ~~频繁全表VACUUM~~ → 依赖autovacuum
5. ~~删除热数据~~ → 归档后再删除

---

## 📞 故障排查

### 问题1: 查询超时

**症状**: 查询话单时超过30秒无响应

**排查步骤**:
1. 检查查询时间范围是否过大（>31天）
2. 查看是否有锁表操作正在进行
3. 检查索引是否存在

```sql
-- 查看当前锁
SELECT * FROM pg_locks WHERE relation::regclass::text = 'cdrs';

-- 查看当前运行的查询
SELECT pid, now() - query_start as duration, query 
FROM pg_stat_activity 
WHERE query LIKE '%cdrs%' AND state = 'active';
```

### 问题2: 同步失败

**症状**: Celery日志显示话单同步任务失败

**排查步骤**:
1. 检查VOS API是否正常
2. 查看是否有重复数据（hash冲突）
3. 检查数据库空间是否充足

```bash
# 查看Celery Worker日志
docker-compose logs -f celery-worker | grep "sync_cdrs"

# 查看数据库空间
docker-compose exec postgres df -h

# 检查表大小
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
  SELECT pg_size_pretty(pg_database_size('vosadmin'));
"
```

### 问题3: 内存不足

**症状**: 查询大量数据时内存溢出

**解决方案**:
- ✅ 使用分页，减少单次查询量
- ✅ 增加PostgreSQL `work_mem` 配置
- ✅ 优化查询条件，使用索引

---

## 📚 相关文档

- 📖 **详细优化方案**: `CDR_OPTIMIZATION_PLAN.md`
- 🚀 **功能总结**: `FEATURE_SUMMARY.md`
- 📋 **部署指南**: `DEPLOYMENT_UPDATE_GUIDE.md`
- 📖 **项目README**: `README.md`

---

**最后更新**: 2025-10-23
**版本**: v1.0
**维护**: YK-VOS Team

