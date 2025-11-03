# 统一话单费用统计表说明

## 概述

统一的话单费用统计表 (`cdr_statistics`) 将原来分散的3张表合并为一张表：
- `vos_cdr_statistics` (VOS节点级别)
- `account_cdr_statistics` (账户级别)  
- `gateway_cdr_statistics` (网关级别)

使用 `statistic_type` 字段区分统计维度，简化了数据管理和查询。

## 表结构

### 关键字段

- **statistic_type**: 统计类型
  - `vos`: VOS节点级别统计（dimension_value 为 NULL）
  - `account`: 账户级别统计（dimension_value 为账户名称）
  - `gateway`: 网关级别统计（dimension_value 为网关名称）

- **dimension_value**: 维度值
  - 当 `statistic_type = 'vos'` 时，为 `NULL`
  - 当 `statistic_type = 'account'` 时，为账户名称
  - 当 `statistic_type = 'gateway'` 时，为网关名称

## 部署步骤

### 1. 全新安装

如果是全新安装，直接执行：

```bash
docker compose exec -T postgres psql -U vos_user -d vosadmin < sql/create_unified_cdr_statistics_table.sql
```

### 2. 从旧表迁移

如果已有旧的3张统计表数据，执行迁移：

```bash
# 步骤1：创建新表
docker compose exec -T postgres psql -U vos_user -d vosadmin < sql/create_unified_cdr_statistics_table.sql

# 步骤2：迁移数据（可选，如需保留旧数据）
docker compose exec -T postgres psql -U vos_user -d vosadmin < sql/migrate_to_unified_cdr_statistics.sql
```

### 3. 更新代码

更新统计任务使用统一表：

```python
# 在 celery_app.py 中更新任务配置
'task': 'app.tasks.unified_cdr_statistics_tasks.calculate_cdr_statistics_unified'
```

## 数据查询示例

### 查询VOS节点统计

```sql
SELECT * FROM cdr_statistics 
WHERE vos_id = 1 
  AND statistic_type = 'vos' 
  AND period_type = 'day'
ORDER BY statistic_date DESC;
```

### 查询账户统计

```sql
SELECT * FROM cdr_statistics 
WHERE vos_id = 1 
  AND statistic_type = 'account' 
  AND dimension_value = '账户名称'
  AND period_type = 'day'
ORDER BY statistic_date DESC;
```

### 查询网关统计

```sql
SELECT * FROM cdr_statistics 
WHERE vos_id = 1 
  AND statistic_type = 'gateway' 
  AND dimension_value = '网关名称'
  AND period_type = 'day'
ORDER BY statistic_date DESC;
```

### 统一查询所有类型

```sql
SELECT 
    statistic_type,
    dimension_value,
    statistic_date,
    SUM(total_fee) as total_fee,
    SUM(total_duration) as total_duration
FROM cdr_statistics
WHERE vos_id = 1
  AND statistic_date >= '2025-01-01'
GROUP BY statistic_type, dimension_value, statistic_date
ORDER BY statistic_date DESC;
```

## 优势

1. **统一管理**：一张表管理所有统计数据，简化维护
2. **灵活查询**：可以轻松跨维度查询和聚合
3. **扩展性强**：新增统计维度只需添加新的 `statistic_type` 值
4. **性能优化**：通过复合索引优化常见查询场景

## 注意事项

- 迁移前请备份数据库
- 迁移完成后，可以选择保留原表作为备份，或删除原表
- 确保应用代码已更新为使用统一表模型

