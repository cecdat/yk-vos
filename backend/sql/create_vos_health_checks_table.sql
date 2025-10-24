-- VOS实例健康检查表
-- 用于存储VOS实例的健康状态

CREATE TABLE IF NOT EXISTS vos_health_checks (
    id SERIAL PRIMARY KEY,
    vos_instance_id INTEGER NOT NULL REFERENCES vos_instances(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'unknown',
    last_check_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_time_ms DOUBLE PRECISION,
    error_message VARCHAR(500),
    api_success BOOLEAN DEFAULT FALSE,
    consecutive_failures INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_vos_health_checks_id ON vos_health_checks(id);
CREATE INDEX IF NOT EXISTS ix_vos_health_checks_vos_instance_id ON vos_health_checks(vos_instance_id);

-- 添加注释
COMMENT ON TABLE vos_health_checks IS 'VOS实例健康检查记录表';
COMMENT ON COLUMN vos_health_checks.vos_instance_id IS 'VOS实例ID';
COMMENT ON COLUMN vos_health_checks.status IS '健康状态: healthy, unhealthy, unknown';
COMMENT ON COLUMN vos_health_checks.last_check_at IS '最后一次检查时间';
COMMENT ON COLUMN vos_health_checks.response_time_ms IS 'API响应时间（毫秒）';
COMMENT ON COLUMN vos_health_checks.error_message IS '错误信息';
COMMENT ON COLUMN vos_health_checks.api_success IS 'API调用是否成功';
COMMENT ON COLUMN vos_health_checks.consecutive_failures IS '连续失败次数';

