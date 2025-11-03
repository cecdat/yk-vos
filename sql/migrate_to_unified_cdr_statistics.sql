-- 迁移脚本：将原有的3张统计表合并到统一的 cdr_statistics 表
-- 执行前请先创建新表：create_unified_cdr_statistics_table.sql

-- 1. 迁移 VOS 节点统计
INSERT INTO cdr_statistics (
    vos_id, vos_uuid, statistic_date, period_type, statistic_type, dimension_value,
    total_fee, total_duration, total_calls, connected_calls, connection_rate,
    created_at, updated_at
)
SELECT 
    vos_id, vos_uuid, statistic_date, period_type, 'vos'::VARCHAR(20), NULL,
    total_fee, total_duration, total_calls, connected_calls, connection_rate,
    created_at, updated_at
FROM vos_cdr_statistics
ON CONFLICT (vos_uuid, statistic_type, dimension_value, statistic_date, period_type) 
DO UPDATE SET
    total_fee = EXCLUDED.total_fee,
    total_duration = EXCLUDED.total_duration,
    total_calls = EXCLUDED.total_calls,
    connected_calls = EXCLUDED.connected_calls,
    connection_rate = EXCLUDED.connection_rate,
    updated_at = EXCLUDED.updated_at;

-- 2. 迁移账户统计
INSERT INTO cdr_statistics (
    vos_id, vos_uuid, statistic_date, period_type, statistic_type, dimension_value,
    total_fee, total_duration, total_calls, connected_calls, connection_rate,
    created_at, updated_at
)
SELECT 
    vos_id, vos_uuid, statistic_date, period_type, 'account'::VARCHAR(20), account_name,
    total_fee, total_duration, total_calls, connected_calls, connection_rate,
    created_at, updated_at
FROM account_cdr_statistics
ON CONFLICT (vos_uuid, statistic_type, dimension_value, statistic_date, period_type) 
DO UPDATE SET
    total_fee = EXCLUDED.total_fee,
    total_duration = EXCLUDED.total_duration,
    total_calls = EXCLUDED.total_calls,
    connected_calls = EXCLUDED.connected_calls,
    connection_rate = EXCLUDED.connection_rate,
    updated_at = EXCLUDED.updated_at;

-- 3. 迁移网关统计
INSERT INTO cdr_statistics (
    vos_id, vos_uuid, statistic_date, period_type, statistic_type, dimension_value,
    total_fee, total_duration, total_calls, connected_calls, connection_rate,
    created_at, updated_at
)
SELECT 
    vos_id, vos_uuid, statistic_date, period_type, 'gateway'::VARCHAR(20), callee_gateway,
    total_fee, total_duration, total_calls, connected_calls, connection_rate,
    created_at, updated_at
FROM gateway_cdr_statistics
ON CONFLICT (vos_uuid, statistic_type, dimension_value, statistic_date, period_type) 
DO UPDATE SET
    total_fee = EXCLUDED.total_fee,
    total_duration = EXCLUDED.total_duration,
    total_calls = EXCLUDED.total_calls,
    connected_calls = EXCLUDED.connected_calls,
    connection_rate = EXCLUDED.connection_rate,
    updated_at = EXCLUDED.updated_at;

-- 注意：迁移完成后，可以选择保留原表作为备份，或者删除原表
-- 删除原表（可选，建议先备份）：
-- DROP TABLE IF EXISTS vos_cdr_statistics;
-- DROP TABLE IF EXISTS account_cdr_statistics;
-- DROP TABLE IF EXISTS gateway_cdr_statistics;

