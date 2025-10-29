-- ClickHouse 表结构升级脚本 - 添加 vos_uuid 支持
-- 执行时间: 2025-01-XX
-- 说明: 为 ClickHouse cdrs 表添加 vos_uuid 字段，支持 VOS 节点唯一标识

-- 1. 添加 vos_uuid 字段到 cdrs 表
ALTER TABLE cdrs ADD COLUMN IF NOT EXISTS vos_uuid String COMMENT 'VOS节点唯一标识';

-- 2. 添加索引提高查询性能
ALTER TABLE cdrs ADD INDEX IF NOT EXISTS idx_vos_uuid vos_uuid TYPE minmax GRANULARITY 4;

-- 3. 更新物化视图以包含 vos_uuid
-- 注意：ClickHouse 不支持直接修改物化视图，需要重建

-- 删除现有的物化视图
DROP VIEW IF EXISTS cdrs_daily_stats;
DROP VIEW IF EXISTS cdrs_account_stats;
DROP VIEW IF EXISTS cdrs_gateway_stats;

-- 重新创建物化视图 - 按天统计（包含 vos_uuid）
CREATE MATERIALIZED VIEW IF NOT EXISTS cdrs_daily_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(call_date)
ORDER BY (vos_id, vos_uuid, call_date, account)
POPULATE
AS SELECT
    vos_id,
    vos_uuid,
    toDate(start) AS call_date,
    account,
    count() AS call_count,
    sum(hold_time) AS total_duration,
    sum(fee) AS total_fee,
    max(start) AS last_call_time
FROM cdrs
GROUP BY vos_id, vos_uuid, call_date, account;

-- 重新创建物化视图 - 按账户实时统计（包含 vos_uuid）
CREATE MATERIALIZED VIEW IF NOT EXISTS cdrs_account_stats
ENGINE = SummingMergeTree()
ORDER BY (vos_id, vos_uuid, account)
POPULATE
AS SELECT
    vos_id,
    vos_uuid,
    account,
    count() AS call_count,
    sum(hold_time) AS total_duration,
    sum(fee) AS total_fee,
    max(start) AS last_call_time
FROM cdrs
GROUP BY vos_id, vos_uuid, account;

-- 重新创建物化视图 - 网关统计（包含 vos_uuid）
CREATE MATERIALIZED VIEW IF NOT EXISTS cdrs_gateway_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(call_date)
ORDER BY (vos_id, vos_uuid, call_date, callee_gateway)
POPULATE
AS SELECT
    vos_id,
    vos_uuid,
    toDate(start) AS call_date,
    callee_gateway,
    count() AS call_count,
    sum(hold_time) AS total_duration,
    sum(fee) AS total_fee
FROM cdrs
GROUP BY vos_id, vos_uuid, call_date, callee_gateway;

-- 完成提示
SELECT 'ClickHouse 表结构升级完成 - 已添加 vos_uuid 支持' as status;
