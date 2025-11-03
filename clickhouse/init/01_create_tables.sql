-- ClickHouse 话单数据库初始化脚本
-- 适用于 YK-VOS 项目

-- 创建数据库
CREATE DATABASE IF NOT EXISTS vos_cdrs;

-- 切换到数据库
USE vos_cdrs;

-- CDR 话单表（使用 ReplacingMergeTree 自动去重）
CREATE TABLE IF NOT EXISTS cdrs
(
    -- 基础字段
    id UInt64 COMMENT '唯一标识（根据flowNo生成）',
    vos_id UInt32 COMMENT 'VOS实例ID',
    vos_uuid String COMMENT 'VOS节点唯一标识',
    flow_no String COMMENT '话单流水号（VOS原始ID）',
    
    -- 账户信息
    account_name String COMMENT '账户名称',
    account String COMMENT '账户号码',
    
    -- 呼叫信息
    caller_e164 String COMMENT '主叫号码',
    caller_access_e164 String COMMENT '主叫接入号码',
    callee_e164 String COMMENT '被叫号码',
    callee_access_e164 String COMMENT '被叫接入号码',
    
    -- 时间信息（分区键）
    start DateTime COMMENT '呼叫开始时间',
    stop DateTime COMMENT '呼叫结束时间',
    
    -- 时长和费用
    hold_time UInt32 COMMENT '通话时长（秒）',
    fee_time UInt32 COMMENT '计费时长（秒）',
    fee Decimal(10, 4) COMMENT '通话费用（元）',
    
    -- 终止信息
    end_reason String COMMENT '终止原因',
    end_direction UInt8 COMMENT '挂断方向（0主叫 1被叫 2服务器）',
    
    -- 网关和IP
    callee_gateway String COMMENT '主叫经由路由',
    callee_ip String COMMENT '被叫IP地址',
    
    -- 原始数据
    raw String COMMENT '原始话单JSON数据',
    
    -- 元数据
    created_at DateTime DEFAULT now() COMMENT '创建时间',
    updated_at DateTime DEFAULT now() COMMENT '更新时间'
)
ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(start)
ORDER BY (vos_id, vos_uuid, start, flow_no)
SETTINGS index_granularity = 8192
COMMENT '话单记录表 - 按月分区，自动去重';

-- 创建跳数索引（加速过滤查询）
ALTER TABLE cdrs ADD INDEX IF NOT EXISTS idx_account account TYPE minmax GRANULARITY 4;
ALTER TABLE cdrs ADD INDEX IF NOT EXISTS idx_caller caller_e164 TYPE minmax GRANULARITY 4;
ALTER TABLE cdrs ADD INDEX IF NOT EXISTS idx_callee callee_access_e164 TYPE minmax GRANULARITY 4;
ALTER TABLE cdrs ADD INDEX IF NOT EXISTS idx_gateway callee_gateway TYPE minmax GRANULARITY 4;
ALTER TABLE cdrs ADD INDEX IF NOT EXISTS idx_vos_uuid vos_uuid TYPE minmax GRANULARITY 4;

-- 创建物化视图 - 按天统计（包含 vos_uuid）
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

-- 创建物化视图 - 按账户实时统计（包含 vos_uuid）
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

-- 创建物化视图 - 网关统计（包含 vos_uuid）
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

