# 话单费用统计表初始化说明

## 执行顺序

1. **首次安装**：在数据库初始化时执行 `create_cdr_statistics_tables.sql`

```bash
docker compose exec postgres psql -U vosadmin -d vosadmin < sql/create_cdr_statistics_tables.sql
```

2. **已存在数据库**：如果数据库已存在，也可以直接执行上述命令（使用了 `IF NOT EXISTS`，不会报错）

## 表结构说明

### 1. vos_cdr_statistics
VOS节点级别的话单统计表
- 按日期和周期类型（日/月/季度/年）统计
- 统计指标：总费用、通话时长、通话数、接通数、接通率

### 2. account_cdr_statistics
账户级别的话单统计表
- 按账户名称、日期、周期类型统计
- 统计指标：同上

### 3. gateway_cdr_statistics
网关级别的话单统计表
- 按落地网关、日期、周期类型统计
- 统计指标：同上

## 定时任务

统计任务配置在 `app/tasks/celery_app.py` 中：
- 任务名称：`calculate-cdr-statistics-daily`
- 执行时间：每天凌晨2点30分
- 任务函数：`app.tasks.cdr_statistics_tasks.calculate_all_instances_statistics`

## 手动触发统计

### 通过API触发

```bash
POST /vos/instances/{instance_id}/statistics/calculate
参数:
- statistic_date: 可选，统计日期 YYYY-MM-DD（默认昨天）
- period_types: 可选，统计周期类型，逗号分隔（默认day）
```

### 通过Celery触发

```python
from app.tasks.cdr_statistics_tasks import calculate_cdr_statistics

# 统计指定VOS节点的昨天日级别数据
calculate_cdr_statistics.delay(instance_id=1, statistic_date=None, period_types=['day'])

# 统计指定日期的多周期数据
from datetime import date
calculate_cdr_statistics.delay(
    instance_id=1,
    statistic_date=date(2025, 1, 1),
    period_types=['day', 'month', 'quarter', 'year']
)
```

## 数据查询

通过API查询统计数据：

```bash
GET /vos/instances/{instance_id}/statistics?period_type=day&start_date=2025-01-01&end_date=2025-01-31
```

返回数据包括：
- `vos_statistics`: VOS节点级别的统计
- `account_statistics`: 账户级别的统计
- `gateway_statistics`: 网关级别的统计

## 接通率计算公式

```
接通率 = (接通通话数 / 总通话记录数) × 100%
```

其中：
- 总通话记录数：所有话单记录（包括未接通）
- 接通通话数：hold_time > 0 的话单记录

