# 上亿级话单数据优化方案

## 📊 问题分析

### 数据规模预估
- **日均话单**: 假设100万条/天
- **年度总量**: 3.65亿条
- **3年累计**: 超过10亿条
- **单条大小**: 约1-2KB（含raw字段）
- **总存储**: 1TB+

### 面临的挑战
1. ❌ 查询性能下降（全表扫描）
2. ❌ 插入速度变慢
3. ❌ 索引体积过大
4. ❌ 备份和恢复困难
5. ❌ 磁盘空间压力

---

## 🎯 优化方案

### 方案1: 数据库分区表（PostgreSQL Partitioning）★★★★★

#### 1.1 按月分区（推荐）

```sql
-- 创建分区主表
CREATE TABLE cdrs_partitioned (
    id BIGSERIAL,
    vos_id INTEGER NOT NULL,
    caller VARCHAR(64),
    callee VARCHAR(64),
    caller_gateway VARCHAR(64),
    callee_gateway VARCHAR(64),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration INTEGER,
    cost NUMERIC(10,4),
    disposition VARCHAR(64),
    raw JSONB,  -- 使用JSONB替代TEXT，支持JSON查询
    hash VARCHAR(32),
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (start_time);

-- 创建分区（按月）
CREATE TABLE cdrs_2025_01 PARTITION OF cdrs_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE cdrs_2025_02 PARTITION OF cdrs_partitioned
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- ... 继续创建更多分区

-- 创建索引（自动应用到所有分区）
CREATE INDEX idx_cdrs_part_vos_time ON cdrs_partitioned(vos_id, start_time);
CREATE INDEX idx_cdrs_part_caller ON cdrs_partitioned(caller);
CREATE INDEX idx_cdrs_part_callee ON cdrs_partitioned(callee);
CREATE INDEX idx_cdrs_part_hash ON cdrs_partitioned(vos_id, hash);
```

**优点**:
- ✅ 查询自动定位到特定分区（查询速度提升10-100倍）
- ✅ 删除老数据只需DROP分区（秒级完成）
- ✅ 维护和备份可按分区进行
- ✅ 索引体积分散，维护成本低

**实现步骤**:
1. 创建新的分区表结构
2. 数据迁移（分批进行）
3. 修改ORM模型
4. 创建自动分区管理脚本

#### 1.2 自动分区管理脚本

```python
# backend/app/scripts/partition_manager.py
from datetime import datetime, timedelta
from app.core.db import SessionLocal

def create_next_month_partition():
    """自动创建下个月的分区"""
    db = SessionLocal()
    try:
        next_month = datetime.now() + timedelta(days=32)
        partition_name = f"cdrs_{next_month.strftime('%Y_%m')}"
        start_date = next_month.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1)
        
        sql = f"""
        CREATE TABLE IF NOT EXISTS {partition_name} 
        PARTITION OF cdrs_partitioned
        FOR VALUES FROM ('{start_date.date()}') TO ('{end_date.date()}');
        """
        
        db.execute(sql)
        db.commit()
        print(f"✅ Created partition: {partition_name}")
    except Exception as e:
        print(f"❌ Failed to create partition: {e}")
    finally:
        db.close()

def cleanup_old_partitions(keep_months=12):
    """删除超过指定月份的旧分区"""
    db = SessionLocal()
    try:
        cutoff_date = datetime.now() - timedelta(days=keep_months*30)
        partition_name = f"cdrs_{cutoff_date.strftime('%Y_%m')}"
        
        # 先导出到归档表
        db.execute(f"""
            CREATE TABLE IF NOT EXISTS cdrs_archive_{partition_name} 
            AS SELECT * FROM {partition_name};
        """)
        
        # 删除分区
        db.execute(f"DROP TABLE {partition_name};")
        db.commit()
        print(f"✅ Archived and dropped partition: {partition_name}")
    except Exception as e:
        print(f"❌ Failed to cleanup partition: {e}")
    finally:
        db.close()
```

---

### 方案2: 数据归档策略 ★★★★★

#### 2.1 冷热数据分离

```python
# 热数据：最近3个月（在主表）
# 温数据：3-12个月（在分区表）
# 冷数据：12个月以上（归档到独立表或对象存储）

class CDRArchiveStrategy:
    """话单归档策略"""
    
    HOT_DATA_MONTHS = 3    # 热数据保留3个月
    WARM_DATA_MONTHS = 12  # 温数据保留12个月
    
    @staticmethod
    def archive_to_cold_storage(months_ago=12):
        """
        归档冷数据到对象存储（如MinIO/S3）
        """
        db = SessionLocal()
        try:
            cutoff_date = datetime.now() - timedelta(days=months_ago*30)
            
            # 1. 导出为Parquet格式（压缩比高）
            query = f"""
                COPY (
                    SELECT * FROM cdrs 
                    WHERE start_time < '{cutoff_date}'
                ) TO PROGRAM 'gzip > /backup/cdrs_{cutoff_date.strftime('%Y%m')}.csv.gz' 
                WITH CSV HEADER;
            """
            db.execute(query)
            
            # 2. 删除已归档数据
            db.execute(f"DELETE FROM cdrs WHERE start_time < '{cutoff_date}'")
            db.commit()
            
            # 3. 上传到对象存储（MinIO/S3）
            # upload_to_s3(f'/backup/cdrs_{cutoff_date.strftime('%Y%m')}.csv.gz')
            
            print(f"✅ Archived data before {cutoff_date}")
        except Exception as e:
            db.rollback()
            print(f"❌ Archive failed: {e}")
        finally:
            db.close()
```

#### 2.2 归档表结构

```sql
-- 创建归档表（仅保留关键字段，去除raw）
CREATE TABLE cdrs_archive (
    id BIGINT,
    vos_id INTEGER,
    caller VARCHAR(64),
    callee VARCHAR(64),
    start_time TIMESTAMP,
    duration INTEGER,
    cost NUMERIC(10,4),
    archived_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (start_time);

-- 压缩归档表
ALTER TABLE cdrs_archive SET (
    autovacuum_enabled = false,
    toast_tuple_target = 8160  -- 最大压缩
);
```

---

### 方案3: 同步策略优化 ★★★★★

#### 3.1 限制同步范围

```python
# backend/app/tasks/initial_sync_tasks.py

@celery.task
def initial_sync_for_new_instance(instance_id: int, days=7):
    """
    新增VOS节点初始化同步
    
    Args:
        instance_id: VOS实例ID
        days: 同步最近多少天（默认7天，不要超过30天）
    """
    # 限制最大同步天数
    if days > 30:
        days = 30
        logger.warning(f"同步天数限制为30天，避免数据量过大")
    
    # ... 同步逻辑
```

#### 3.2 分页批量处理

```python
@celery.task
def sync_cdrs_for_single_day_batch(instance_id: int, date_str: str):
    """
    分页同步单天话单（避免一次性加载过多数据）
    """
    PAGE_SIZE = 1000  # 每次处理1000条
    page = 0
    
    while True:
        # 分页请求VOS API
        result = client.call_api('/external/server/GetCdr', {
            'beginTime': date_str,
            'endTime': date_str,
            'pageNo': page,
            'pageSize': PAGE_SIZE
        })
        
        cdrs = result.get('infoCdrs', [])
        if not cdrs:
            break
        
        # 批量插入（使用bulk_insert_mappings）
        db.bulk_insert_mappings(CDR, [
            {
                'vos_id': instance_id,
                'caller': cdr['callerE164'],
                'callee': cdr['calleeE164'],
                # ... 其他字段
            }
            for cdr in cdrs
        ])
        db.commit()
        
        page += 1
        time.sleep(0.5)  # 避免API限流
```

#### 3.3 增量同步

```python
@celery.task
def incremental_sync_cdrs(instance_id: int):
    """
    增量同步：只同步最后一次同步时间之后的数据
    """
    db = SessionLocal()
    try:
        # 获取最后同步时间
        last_cdr = db.query(CDR).filter(
            CDR.vos_id == instance_id
        ).order_by(CDR.start_time.desc()).first()
        
        if last_cdr:
            begin_time = last_cdr.start_time.strftime('%Y%m%d')
        else:
            # 首次同步，只同步最近7天
            begin_time = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        end_time = datetime.now().strftime('%Y%m%d')
        
        # 同步增量数据
        sync_cdrs_by_date_range(instance_id, begin_time, end_time)
        
    finally:
        db.close()
```

---

### 方案4: 查询优化 ★★★★★

#### 4.1 强制时间范围限制

```python
# backend/app/routers/cdr.py

@router.post('/instances/{instance_id}/cdrs/query')
async def query_cdrs_from_vos(
    instance_id: int,
    query_params: CDRQueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    force_vos: bool = Query(False)
):
    """查询话单（强制时间范围限制）"""
    
    # 解析时间范围
    begin_date = datetime.strptime(query_params.begin_time, '%Y%m%d')
    end_date = datetime.strptime(query_params.end_time, '%Y%m%d')
    
    # 限制查询范围不超过31天
    if (end_date - begin_date).days > 31:
        raise HTTPException(
            status_code=400, 
            detail='查询范围不能超过31天，避免性能问题'
        )
    
    # 限制不能查询超过1年前的数据（引导用户使用归档数据）
    if begin_date < datetime.now() - timedelta(days=365):
        raise HTTPException(
            status_code=400,
            detail='查询1年前的数据请联系管理员访问归档系统'
        )
    
    # ... 查询逻辑
```

#### 4.2 结果集分页

```python
@router.post('/instances/{instance_id}/cdrs/query')
async def query_cdrs_from_vos(
    # ... 参数
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)  # 限制最大100条/页
):
    """查询话单（带分页）"""
    
    offset = (page - 1) * page_size
    
    # 查询总数（使用count优化）
    total = db.query(func.count(CDR.id)).filter(
        CDR.vos_id == instance_id,
        CDR.start_time >= begin_date,
        CDR.start_time <= end_date
    ).scalar()
    
    # 查询分页数据
    cdrs = db.query(CDR).filter(
        CDR.vos_id == instance_id,
        CDR.start_time >= begin_date,
        CDR.start_time <= end_date
    ).order_by(CDR.start_time.desc()).offset(offset).limit(page_size).all()
    
    return {
        'data': cdrs,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size
    }
```

#### 4.3 查询结果缓存

```python
from functools import lru_cache
from redis import Redis

redis_client = Redis(host='redis', port=6379, db=1)

def get_cdr_query_cache(cache_key: str):
    """从Redis获取查询缓存"""
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    return None

def set_cdr_query_cache(cache_key: str, data: dict, ttl=300):
    """设置查询缓存（5分钟）"""
    redis_client.setex(cache_key, ttl, json.dumps(data))
```

---

### 方案5: 数据库参数优化 ★★★★

#### 5.1 PostgreSQL配置优化

```conf
# postgresql.conf

# 内存配置（假设16GB服务器）
shared_buffers = 4GB              # 共享缓冲区
effective_cache_size = 12GB       # 有效缓存大小
work_mem = 256MB                  # 单次操作内存
maintenance_work_mem = 1GB        # 维护操作内存

# 写入优化
wal_buffers = 16MB
checkpoint_timeout = 15min
max_wal_size = 4GB
checkpoint_completion_target = 0.9

# 查询优化
random_page_cost = 1.1            # SSD优化
effective_io_concurrency = 200    # SSD并发
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8

# 日志
log_min_duration_statement = 1000  # 记录慢查询（>1s）
```

#### 5.2 定期维护

```sql
-- 定期VACUUM和ANALYZE（周末执行）
VACUUM ANALYZE cdrs;

-- 重建索引（月度执行）
REINDEX TABLE cdrs;

-- 更新统计信息
ANALYZE cdrs;
```

---

### 方案6: raw字段优化 ★★★★

#### 6.1 使用JSONB替代TEXT

```python
# backend/app/models/cdr.py

from sqlalchemy.dialects.postgresql import JSONB

class CDR(Base):
    __tablename__ = 'cdrs'
    
    # ... 其他字段
    
    # 使用JSONB替代TEXT
    raw = Column(JSONB)  # 支持JSON查询，自动压缩
```

**优点**:
- ✅ 自动压缩，节省30-50%空间
- ✅ 支持JSON字段查询：`raw->>'caller'`
- ✅ 可以创建GIN索引加速JSON查询

#### 6.2 选择性保存raw字段

```python
@celery.task
def sync_cdrs_for_single_day(instance_id: int, date_str: str, save_raw=False):
    """
    同步话单（可选是否保存原始数据）
    
    Args:
        save_raw: 是否保存raw字段（默认False节省空间）
    """
    # ... 同步逻辑
    
    newc = CDR(
        vos_id=inst.id,
        caller=caller,
        callee=callee,
        # ... 其他字段
        raw=c if save_raw else None  # 可选保存raw
    )
```

---

### 方案7: 时序数据库方案（可选）★★★

对于超大规模话单，可考虑使用专门的时序数据库：

#### 7.1 TimescaleDB（PostgreSQL扩展）

```sql
-- 安装TimescaleDB扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 转换为超表（自动分区）
SELECT create_hypertable('cdrs', 'start_time');

-- 自动数据压缩
ALTER TABLE cdrs SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'vos_id',
  timescaledb.compress_orderby = 'start_time DESC'
);

-- 自动压缩策略（30天前的数据自动压缩）
SELECT add_compression_policy('cdrs', INTERVAL '30 days');

-- 数据保留策略（自动删除1年前的数据）
SELECT add_retention_policy('cdrs', INTERVAL '1 year');
```

**优点**:
- ✅ 自动分区和压缩（压缩比10:1）
- ✅ 时序查询性能优异
- ✅ 兼容PostgreSQL语法
- ✅ 自动数据保留策略

#### 7.2 ClickHouse（专业OLAP数据库）

适合大规模分析查询，但需要独立部署。

---

## 📋 实施计划

### 阶段1: 立即实施（1-2天）

- [x] 添加查询时间范围限制（最多31天）
- [x] 添加结果集分页
- [x] 限制新增VOS节点首次同步范围（7天）
- [x] 添加查询结果缓存

### 阶段2: 短期优化（1周）

- [ ] 实施数据库分区表（按月分区）
- [ ] 迁移现有数据到分区表
- [ ] 创建分区管理脚本
- [ ] raw字段改为JSONB

### 阶段3: 中期优化（2-4周）

- [ ] 实施数据归档策略
- [ ] 建立冷数据对象存储
- [ ] 优化数据库配置
- [ ] 建立自动维护任务

### 阶段4: 长期规划（3个月+）

- [ ] 评估TimescaleDB方案
- [ ] 建立数据分析平台
- [ ] 实施更多智能归档策略

---

## 💰 成本与收益分析

### 不优化的代价

| 数据量 | 查询时间 | 插入速度 | 存储空间 |
|--------|----------|----------|----------|
| 1亿条 | 10-30秒 | 慢 | 200GB |
| 5亿条 | 1-5分钟 | 很慢 | 1TB |
| 10亿条 | 超时 | 极慢 | 2TB+ |

### 优化后效果

| 优化措施 | 查询提升 | 存储节省 | 实施难度 |
|----------|----------|----------|----------|
| 分区表 | 10-100倍 | 0% | 中 |
| JSONB | 10-20% | 30-50% | 低 |
| 归档策略 | - | 60-80% | 中 |
| 时间限制 | 显著 | - | 低 |
| TimescaleDB | 100倍+ | 90% | 高 |

---

## 🎯 推荐方案组合

### 最小可行方案（MVP）
1. ✅ 查询时间范围限制（31天）
2. ✅ 结果集分页
3. ✅ 首次同步限制（7天）

### 标准方案（推荐）
1. ✅ 最小可行方案
2. ✅ 数据库分区表（按月）
3. ✅ raw字段JSONB化
4. ✅ 数据归档策略（12个月）

### 企业方案（最优）
1. ✅ 标准方案
2. ✅ TimescaleDB集成
3. ✅ 对象存储归档
4. ✅ 分析查询独立集群

---

## 📝 监控指标

```sql
-- 表大小监控
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename LIKE 'cdrs%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 查询性能监控
SELECT 
    query,
    mean_exec_time,
    calls
FROM pg_stat_statements
WHERE query LIKE '%cdrs%'
ORDER BY mean_exec_time DESC
LIMIT 10;

-- 索引使用率
SELECT 
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public' AND tablename LIKE 'cdrs%';
```

---

需要我帮您实施哪个方案吗？我建议从**标准方案**开始！

