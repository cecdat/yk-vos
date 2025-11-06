-- ClickHouse 升级脚本：为 cdrs 表添加 caller_gateway 字段
-- 适用于已存在的数据库
-- 注意：此脚本需要在 ClickHouse 服务运行后手动执行，或通过后端服务执行

USE vos_cdrs;

-- 注意：ClickHouse 的 ALTER TABLE ADD COLUMN 如果字段已存在会报错
-- 但不会影响服务启动，所以可以安全地执行

-- 添加 caller_gateway 字段（如果不存在，需要手动检查）
-- 执行前请先检查：SELECT * FROM system.columns WHERE database = 'vos_cdrs' AND table = 'cdrs' AND name = 'caller_gateway'
-- 如果查询结果为空，则执行以下语句：
-- ALTER TABLE cdrs ADD COLUMN IF NOT EXISTS caller_gateway String COMMENT '对接网关（主叫网关）';

-- 添加索引（如果不存在）
-- ALTER TABLE cdrs ADD INDEX IF NOT EXISTS idx_caller_gateway caller_gateway TYPE minmax GRANULARITY 4;

-- 注意：物化视图的创建和删除需要谨慎处理
-- 如果物化视图已存在，CREATE MATERIALIZED VIEW IF NOT EXISTS 不会报错
-- 但如果视图结构不同，可能需要先删除再创建

