-- 创建话单费用统计表
-- 用于存储从ClickHouse统计的话单费用、时长、接通率等数据

-- 1. VOS节点级别的统计数据表
CREATE TABLE IF NOT EXISTS vos_cdr_statistics (
    id SERIAL PRIMARY KEY,
    vos_id INTEGER NOT NULL,
    vos_uuid UUID NOT NULL,
    statistic_date DATE NOT NULL,  -- 统计日期
    period_type VARCHAR(10) NOT NULL,  -- 统计周期：day, month, quarter, year
    -- 费用统计
    total_fee DECIMAL(15, 4) DEFAULT 0,  -- 总费用
    -- 时长统计
    total_duration BIGINT DEFAULT 0,  -- 总通话时长（秒，大于0秒的通话）
    total_calls BIGINT DEFAULT 0,  -- 总通话记录数
    connected_calls BIGINT DEFAULT 0,  -- 接通通话数（hold_time > 0）
    -- 接通率
    connection_rate DECIMAL(5, 2) DEFAULT 0,  -- 接通率（百分比）
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- 唯一约束：同一个vos节点、同一天、同一个周期类型只能有一条记录
    CONSTRAINT uq_vos_cdr_statistics UNIQUE (vos_id, vos_uuid, statistic_date, period_type)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_vos_cdr_statistics_vos_id ON vos_cdr_statistics(vos_id);
CREATE INDEX IF NOT EXISTS idx_vos_cdr_statistics_vos_uuid ON vos_cdr_statistics(vos_uuid);
CREATE INDEX IF NOT EXISTS idx_vos_cdr_statistics_date ON vos_cdr_statistics(statistic_date);
CREATE INDEX IF NOT EXISTS idx_vos_cdr_statistics_period ON vos_cdr_statistics(period_type);
CREATE INDEX IF NOT EXISTS idx_vos_cdr_statistics_composite ON vos_cdr_statistics(vos_uuid, statistic_date, period_type);

-- 2. 账户级别的统计数据表
CREATE TABLE IF NOT EXISTS account_cdr_statistics (
    id SERIAL PRIMARY KEY,
    vos_id INTEGER NOT NULL,
    vos_uuid UUID NOT NULL,
    account_name VARCHAR(256) NOT NULL,  -- 账户名称
    statistic_date DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL,
    -- 费用统计
    total_fee DECIMAL(15, 4) DEFAULT 0,
    -- 时长统计
    total_duration BIGINT DEFAULT 0,
    total_calls BIGINT DEFAULT 0,
    connected_calls BIGINT DEFAULT 0,
    -- 接通率
    connection_rate DECIMAL(5, 2) DEFAULT 0,
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_account_cdr_statistics UNIQUE (vos_id, vos_uuid, account_name, statistic_date, period_type)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_account_cdr_statistics_vos_id ON account_cdr_statistics(vos_id);
CREATE INDEX IF NOT EXISTS idx_account_cdr_statistics_vos_uuid ON account_cdr_statistics(vos_uuid);
CREATE INDEX IF NOT EXISTS idx_account_cdr_statistics_account ON account_cdr_statistics(account_name);
CREATE INDEX IF NOT EXISTS idx_account_cdr_statistics_date ON account_cdr_statistics(statistic_date);
CREATE INDEX IF NOT EXISTS idx_account_cdr_statistics_composite ON account_cdr_statistics(vos_uuid, account_name, statistic_date, period_type);

-- 3. 网关级别的统计数据表
CREATE TABLE IF NOT EXISTS gateway_cdr_statistics (
    id SERIAL PRIMARY KEY,
    vos_id INTEGER NOT NULL,
    vos_uuid UUID NOT NULL,
    callee_gateway VARCHAR(256) NOT NULL,  -- 落地网关
    statistic_date DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL,
    -- 费用统计
    total_fee DECIMAL(15, 4) DEFAULT 0,
    -- 时长统计
    total_duration BIGINT DEFAULT 0,
    total_calls BIGINT DEFAULT 0,
    connected_calls BIGINT DEFAULT 0,
    -- 接通率
    connection_rate DECIMAL(5, 2) DEFAULT 0,
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_gateway_cdr_statistics UNIQUE (vos_id, vos_uuid, callee_gateway, statistic_date, period_type)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_gateway_cdr_statistics_vos_id ON gateway_cdr_statistics(vos_id);
CREATE INDEX IF NOT EXISTS idx_gateway_cdr_statistics_vos_uuid ON gateway_cdr_statistics(vos_uuid);
CREATE INDEX IF NOT EXISTS idx_gateway_cdr_statistics_gateway ON gateway_cdr_statistics(callee_gateway);
CREATE INDEX IF NOT EXISTS idx_gateway_cdr_statistics_date ON gateway_cdr_statistics(statistic_date);
CREATE INDEX IF NOT EXISTS idx_gateway_cdr_statistics_composite ON gateway_cdr_statistics(vos_uuid, callee_gateway, statistic_date, period_type);

COMMENT ON TABLE vos_cdr_statistics IS 'VOS节点话单费用统计表';
COMMENT ON TABLE account_cdr_statistics IS '账户话单费用统计表';
COMMENT ON TABLE gateway_cdr_statistics IS '网关话单费用统计表';

