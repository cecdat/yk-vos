-- ====================================
-- YK-VOS 数据库初始化脚本
-- 适用于全新服务器部署
-- 
-- 执行说明：
-- 1. 此脚本在Alembic迁移之前执行，只创建基础表结构（扩展、统计表、版本管理表）
-- 2. Alembic迁移会在应用启动时自动执行，创建所有业务表
-- 3. Alembic迁移0011会为所有表添加vos_uuid字段
-- 
-- 执行顺序：
-- 1. 启动数据库服务
-- 2. 执行此脚本（init_database.sql）
-- 3. 启动应用
-- 4. 应用启动时自动执行Alembic迁移
-- ====================================

-- 1. 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 用于全文搜索

-- 2. 创建统一的话单费用统计表
-- 将VOS节点、账户、网关三个级别的统计数据合并到一张表
CREATE TABLE IF NOT EXISTS cdr_statistics (
    id SERIAL PRIMARY KEY,
    
    -- 基础关联字段
    vos_id INTEGER NOT NULL,
    vos_uuid UUID NOT NULL,
    statistic_date DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL,  -- 统计周期：day, month, quarter, year
    
    -- 统计维度类型
    statistic_type VARCHAR(20) NOT NULL,  -- 统计类型：vos, account, gateway
    
    -- 维度标识字段（根据 statistic_type 使用不同的字段）
    -- 当 statistic_type = 'vos' 时，dimension_value 为空
    -- 当 statistic_type = 'account' 时，dimension_value 存储账户名称
    -- 当 statistic_type = 'gateway' 时，dimension_value 存储网关名称
    dimension_value VARCHAR(256),  -- 维度值（账户名称或网关名称）
    
    -- 统计指标
    total_fee DECIMAL(15, 4) DEFAULT 0,  -- 总费用
    total_duration BIGINT DEFAULT 0,  -- 总通话时长（秒，大于0秒的通话）
    total_calls BIGINT DEFAULT 0,  -- 总通话记录数
    connected_calls BIGINT DEFAULT 0,  -- 接通通话数（hold_time > 0）
    connection_rate DECIMAL(5, 2) DEFAULT 0,  -- 接通率（百分比）
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一约束：确保同一维度、同一日期、同一周期类型只有一条记录
    CONSTRAINT uq_cdr_statistics UNIQUE (vos_uuid, statistic_type, dimension_value, statistic_date, period_type)
);

-- 基础索引
CREATE INDEX IF NOT EXISTS idx_cdr_statistics_vos_id ON cdr_statistics(vos_id);
CREATE INDEX IF NOT EXISTS idx_cdr_statistics_vos_uuid ON cdr_statistics(vos_uuid);
CREATE INDEX IF NOT EXISTS idx_cdr_statistics_date ON cdr_statistics(statistic_date);
CREATE INDEX IF NOT EXISTS idx_cdr_statistics_period ON cdr_statistics(period_type);
CREATE INDEX IF NOT EXISTS idx_cdr_statistics_type ON cdr_statistics(statistic_type);
CREATE INDEX IF NOT EXISTS idx_cdr_statistics_dimension ON cdr_statistics(dimension_value);

-- 复合索引（优化查询性能）
CREATE INDEX IF NOT EXISTS idx_cdr_statistics_vos_composite ON cdr_statistics(vos_uuid, statistic_date, period_type, statistic_type);
CREATE INDEX IF NOT EXISTS idx_cdr_statistics_account_composite ON cdr_statistics(vos_uuid, statistic_type, dimension_value, statistic_date, period_type) 
    WHERE statistic_type = 'account';
CREATE INDEX IF NOT EXISTS idx_cdr_statistics_gateway_composite ON cdr_statistics(vos_uuid, statistic_type, dimension_value, statistic_date, period_type) 
    WHERE statistic_type = 'gateway';

-- 表注释
COMMENT ON TABLE cdr_statistics IS '统一的话单费用统计表（VOS节点/账户/网关三级统计）';
COMMENT ON COLUMN cdr_statistics.statistic_type IS '统计类型：vos(节点), account(账户), gateway(网关)';
COMMENT ON COLUMN cdr_statistics.dimension_value IS '维度值：account时为账户名称，gateway时为网关名称，vos时为空';

-- 3. 创建数据库版本管理表
CREATE TABLE IF NOT EXISTS db_versions (
    version VARCHAR(20) PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(100) DEFAULT CURRENT_USER
);

COMMENT ON TABLE db_versions IS '数据库版本管理表，记录所有已应用的迁移版本';

-- 插入初始版本记录（如果不存在）
INSERT INTO db_versions (version, description) 
VALUES ('2.4', '初始化：创建统一统计表和版本管理表')
ON CONFLICT (version) DO NOTHING;

-- 完成提示
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '数据库初始化完成';
    RAISE NOTICE '- 统一统计表已创建';
    RAISE NOTICE '- 版本管理表已创建';
    RAISE NOTICE '========================================';
END $$;

