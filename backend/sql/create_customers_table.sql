-- 创建客户数据表
-- 用于本地缓存VOS客户数据，提升查询性能

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    vos_instance_id INTEGER NOT NULL REFERENCES vos_instances(id) ON DELETE CASCADE,
    
    -- 客户基本信息
    account VARCHAR(255) NOT NULL,
    money DOUBLE PRECISION DEFAULT 0.0,
    limit_money DOUBLE PRECISION DEFAULT 0.0,
    
    -- 状态标记
    is_in_debt BOOLEAN DEFAULT FALSE,
    
    -- 时间戳
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一约束：同一个VOS实例中账户名唯一
    CONSTRAINT unique_vos_account UNIQUE (vos_instance_id, account)
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_customers_vos_id ON customers(vos_instance_id);
CREATE INDEX IF NOT EXISTS idx_customers_account ON customers(account);
CREATE INDEX IF NOT EXISTS idx_customers_is_in_debt ON customers(is_in_debt);
CREATE INDEX IF NOT EXISTS idx_customers_vos_account ON customers(vos_instance_id, account);
CREATE INDEX IF NOT EXISTS idx_customers_vos_debt ON customers(vos_instance_id, is_in_debt);

-- 注释
COMMENT ON TABLE customers IS 'VOS客户数据本地缓存表';
COMMENT ON COLUMN customers.vos_instance_id IS '关联的VOS实例ID';
COMMENT ON COLUMN customers.account IS '客户账号';
COMMENT ON COLUMN customers.money IS '当前余额';
COMMENT ON COLUMN customers.limit_money IS '授信额度';
COMMENT ON COLUMN customers.is_in_debt IS '是否欠费(money<0)';
COMMENT ON COLUMN customers.synced_at IS '最后同步时间';

