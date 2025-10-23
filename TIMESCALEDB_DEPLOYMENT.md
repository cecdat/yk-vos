# TimescaleDB 部署指南

## 📋 概述

本项目已完全集成TimescaleDB，替代了原PostgreSQL数据库。TimescaleDB是PostgreSQL的超级扩展，专为时序数据优化，特别适合上亿级话单数据。

### 🚀 核心优势

| 特性 | PostgreSQL | TimescaleDB | 提升 |
|------|------------|-------------|------|
| **查询性能** | 慢 | 快 | 10-100倍 |
| **存储压缩** | 无 | 自动 | 压缩比10:1 |
| **数据分区** | 手动 | 自动 | 按时间自动 |
| **数据保留** | 手动删除 | 自动策略 | 无需干预 |
| **数据清理** | VACUUM慢 | 自动优化 | 性能稳定 |

---

## 🏗️ 架构变更

### CDR表结构（全新重构）

```sql
CREATE TABLE cdrs (
    -- 主键和外键
    id INTEGER PRIMARY KEY,                    -- 自增主键
    vos_id INTEGER NOT NULL,                   -- VOS实例ID
    
    -- 账户信息
    account_name VARCHAR(128),                 -- 账户名称
    account VARCHAR(64),                       -- 账户号码
    
    -- 呼叫信息
    caller_e164 VARCHAR(64),                   -- 主叫号码
    callee_access_e164 VARCHAR(64),            -- 被叫号码
    
    -- 时间信息（TimescaleDB分区键）
    start TIMESTAMP NOT NULL,                  -- 起始时间 ⭐ 主分区键
    stop TIMESTAMP,                            -- 终止时间
    
    -- 时长和费用
    hold_time INTEGER,                         -- 通话时长(秒)
    fee_time INTEGER,                          -- 计费时长(秒)
    fee NUMERIC(10,4),                         -- 通话费用
    
    -- 终止信息
    end_reason VARCHAR(128),                   -- 终止原因
    end_direction SMALLINT,                    -- 挂断方(0主叫,1被叫,2服务器)
    
    -- 网关和IP
    callee_gateway VARCHAR(64),                -- 主叫经由路由
    callee_ip VARCHAR(64),                     -- 被叫IP地址
    
    -- 原始数据和唯一标识
    raw JSONB,                                 -- 原始话单数据(JSONB格式) ⭐ 自动压缩
    flow_no VARCHAR(64) UNIQUE NOT NULL        -- 话单唯一标识 ⭐ 去重键
);
```

### TimescaleDB超表特性

```sql
-- 1. 自动分区（每7天一个chunk）
SELECT create_hypertable('cdrs', 'start', chunk_time_interval => INTERVAL '7 days');

-- 2. 自动压缩（30天后压缩）
ALTER TABLE cdrs SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'vos_id',
    timescaledb.compress_orderby = 'start DESC, flow_no'
);
SELECT add_compression_policy('cdrs', INTERVAL '30 days');

-- 3. 自动删除（1年后删除）
SELECT add_retention_policy('cdrs', INTERVAL '1 year');

-- 4. 连续聚合（每小时统计）
CREATE MATERIALIZED VIEW cdrs_hourly_stats
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', start) AS hour,
    vos_id,
    account,
    COUNT(*) as call_count,
    SUM(hold_time) as total_hold_time,
    SUM(fee) as total_fee,
    AVG(hold_time) as avg_hold_time
FROM cdrs
GROUP BY hour, vos_id, account;
```

---

## 🚀 全新初始化部署（推荐）

### 方法1: 使用init-deploy.sh（一键部署）

```bash
# 1. 克隆或上传代码到服务器
cd /data
git clone https://github.com/your-repo/yk-vos.git
cd yk-vos

# 2. 运行初始化部署脚本
chmod +x init-deploy.sh
./init-deploy.sh
```

脚本将自动：
- ✅ 检查Docker和Docker Compose
- ✅ 生成.env配置文件
- ✅ 构建基础镜像
- ✅ 启动所有服务（包括TimescaleDB）
- ✅ 运行数据库迁移（自动创建TimescaleDB超表）
- ✅ 创建默认管理员账户
- ✅ 验证部署状态

### 方法2: 手动部署

```bash
# 1. 创建.env文件
cat > .env << 'EOF'
# 数据库配置
POSTGRES_USER=vos_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=vosadmin

# 应用配置
SECRET_KEY=your_secret_key_change_this
DEBUG=False

# Redis配置
REDIS_URL=redis://redis:6379

# 数据库连接（使用TimescaleDB）
DATABASE_URL=postgresql://vos_user:your_secure_password_here@postgres:5432/vosadmin
EOF

# 2. 创建数据目录
mkdir -p data/postgres

# 3. 构建基础镜像
docker-compose -f docker-compose.base.yaml build

# 4. 启动所有服务
docker-compose up -d

# 5. 等待数据库就绪
sleep 10

# 6. 数据库迁移会自动执行（通过docker-entrypoint.sh）
# 可以通过日志查看进度
docker-compose logs -f backend | grep -i "alembic\|timescale"

# 7. 验证TimescaleDB
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dx timescaledb"
docker-compose exec postgres psql -U vos_user -d vosadmin -c "SELECT * FROM timescaledb_information.hypertables;"
```

---

## 🔄 从旧版本升级到TimescaleDB

### ⚠️ 重要提醒

**此操作将重建cdrs表，现有话单数据将被备份但不会自动迁移！**

如果您已有大量话单数据，建议：
1. 先备份现有数据
2. 使用全新初始化部署
3. 通过VOS API重新同步最近1个月的数据

### 升级步骤

```bash
# 1. 停止所有服务
docker-compose down

# 2. 备份数据（重要！）
docker-compose up -d postgres
sleep 5
docker-compose exec postgres pg_dump -U vos_user -d vosadmin -t cdrs > cdrs_backup_$(date +%Y%m%d).sql
docker-compose exec postgres pg_dump -U vos_user -d vosadmin > full_backup_$(date +%Y%m%d).sql
docker-compose down

# 3. 清理旧数据（可选，如果想全新开始）
sudo rm -rf data/postgres/*

# 4. 更新代码
git pull origin main

# 5. 更新docker-compose.yaml（已包含TimescaleDB镜像）

# 6. 重新启动服务
docker-compose up -d

# 7. 等待数据库迁移完成
docker-compose logs -f backend | grep "alembic upgrade head"

# 8. 验证TimescaleDB超表创建
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
    SELECT hypertable_name, 
           num_dimensions, 
           num_chunks,
           compression_enabled
    FROM timescaledb_information.hypertables 
    WHERE hypertable_name = 'cdrs';
"

# 9. 查看表结构
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\d+ cdrs"
```

---

## 📊 性能验证

### 1. 查看超表状态

```bash
docker-compose exec postgres psql -U vos_user -d vosadmin << 'SQL'
-- 查看超表信息
SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'cdrs';

-- 查看chunks（分区）
SELECT * FROM timescaledb_information.chunks WHERE hypertable_name = 'cdrs';

-- 查看压缩状态
SELECT * FROM timescaledb_information.compression_settings WHERE hypertable_name = 'cdrs';
SQL
```

### 2. 性能测试

```bash
# 插入测试数据（1000条）
docker-compose exec postgres psql -U vos_user -d vosadmin << 'SQL'
INSERT INTO cdrs (vos_id, caller_e164, callee_access_e164, start, hold_time, fee, flow_no)
SELECT 
    1,
    '1380000' || (i % 10000)::text,
    '1390000' || (i % 10000)::text,
    NOW() - (i || ' hours')::INTERVAL,
    floor(random() * 3600)::int,
    random() * 100,
    'FLOW_' || i::text
FROM generate_series(1, 1000) i;
SQL

# 查询性能测试
time docker-compose exec postgres psql -U vos_user -d vosadmin -c "
    SELECT COUNT(*), AVG(hold_time), SUM(fee) 
    FROM cdrs 
    WHERE start >= NOW() - INTERVAL '7 days';
"
```

### 3. 查看表大小

```bash
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
    SELECT 
        pg_size_pretty(pg_total_relation_size('cdrs')) as total_size,
        pg_size_pretty(pg_relation_size('cdrs')) as table_size,
        pg_size_pretty(pg_total_relation_size('cdrs') - pg_relation_size('cdrs')) as index_size;
"
```

---

## 🎯 TimescaleDB特有功能

### 1. 时间桶查询（超快聚合）

```sql
-- 每小时话单统计
SELECT 
    time_bucket('1 hour', start) AS hour,
    COUNT(*) as call_count,
    AVG(hold_time) as avg_duration,
    SUM(fee) as total_fee
FROM cdrs
WHERE start >= NOW() - INTERVAL '1 day'
GROUP BY hour
ORDER BY hour DESC;

-- 每天话单统计
SELECT 
    time_bucket('1 day', start) AS day,
    vos_id,
    COUNT(*) as calls,
    SUM(fee) as revenue
FROM cdrs
WHERE start >= NOW() - INTERVAL '30 days'
GROUP BY day, vos_id
ORDER BY day DESC;
```

### 2. 连续聚合视图（实时统计）

```sql
-- 查询预聚合结果（极快）
SELECT * FROM cdrs_hourly_stats 
WHERE hour >= NOW() - INTERVAL '24 hours'
ORDER BY hour DESC;

-- 刷新聚合视图
CALL refresh_continuous_aggregate('cdrs_hourly_stats', NOW() - INTERVAL '7 days', NOW());
```

### 3. 数据保留查看

```sql
-- 查看保留策略
SELECT * FROM timescaledb_information.jobs 
WHERE proc_name = 'policy_retention';

-- 手动触发压缩
SELECT compress_chunk(i.show_chunks) 
FROM show_chunks('cdrs', older_than => INTERVAL '30 days') i;
```

### 4. 查看压缩率

```sql
SELECT 
    pg_size_pretty(before_compression_total_bytes) as before,
    pg_size_pretty(after_compression_total_bytes) as after,
    round((1 - after_compression_total_bytes::numeric / before_compression_total_bytes) * 100, 2) as compression_ratio
FROM timescaledb_information.compression_settings
WHERE hypertable_name = 'cdrs';
```

---

## 🔧 日常运维

### 查看chunk状态

```bash
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
    SELECT 
        chunk_name,
        range_start,
        range_end,
        is_compressed,
        pg_size_pretty(total_bytes) as size
    FROM timescaledb_information.chunks 
    WHERE hypertable_name = 'cdrs'
    ORDER BY range_start DESC
    LIMIT 10;
"
```

### 手动压缩旧数据

```bash
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
    SELECT compress_chunk(i) 
    FROM show_chunks('cdrs', older_than => INTERVAL '30 days') i;
"
```

### 删除旧chunk（已有自动策略）

```bash
# 查看将被删除的chunks
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
    SELECT * FROM show_chunks('cdrs', older_than => INTERVAL '1 year');
"

# 手动删除（一般不需要，自动策略会处理）
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
    SELECT drop_chunks('cdrs', older_than => INTERVAL '1 year');
"
```

---

## 📈 监控和告警

### 关键指标

```sql
-- 超表健康检查
SELECT 
    hypertable_name,
    num_chunks,
    num_dimensions,
    compression_enabled
FROM timescaledb_information.hypertables;

-- chunks大小分布
SELECT 
    chunk_name,
    pg_size_pretty(total_bytes) as size,
    is_compressed,
    range_start,
    range_end
FROM timescaledb_information.chunks
WHERE hypertable_name = 'cdrs'
ORDER BY total_bytes DESC
LIMIT 10;

-- 后台任务状态
SELECT 
    job_id,
    proc_name,
    scheduled,
    last_run_status,
    last_run_started_at,
    last_run_duration
FROM timescaledb_information.jobs;
```

---

## 🚨 故障排查

### 问题1: TimescaleDB扩展未安装

**症状**: `ERROR: extension "timescaledb" does not exist`

**解决**:
```bash
docker-compose exec postgres psql -U vos_user -d vosadmin -c "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"
```

### 问题2: 超表未创建

**症状**: `ERROR: relation "cdrs" is not a hypertable`

**解决**:
```bash
# 重新运行迁移
docker-compose exec backend alembic upgrade head
```

### 问题3: 压缩策略未生效

**检查**:
```bash
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
    SELECT * FROM timescaledb_information.jobs 
    WHERE proc_name = 'policy_compression';
"
```

**修复**:
```bash
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
    SELECT add_compression_policy('cdrs', INTERVAL '30 days');
"
```

---

## 📚 相关文档

- 📖 **优化方案**: `CDR_OPTIMIZATION_PLAN.md`
- 📋 **快速参考**: `QUICK_REFERENCE_CDR.md`
- 🚀 **部署指南**: `DEPLOYMENT_UPDATE_GUIDE.md`
- 📘 **TimescaleDB官方文档**: https://docs.timescale.com/

---

**最后更新**: 2025-10-23
**版本**: v2.0 (TimescaleDB)

