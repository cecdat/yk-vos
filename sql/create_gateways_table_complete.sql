-- ====================================
-- gateways表完整创建脚本（包含所有扩展字段）
-- 说明：此脚本包含gateways表的完整定义，包括所有扩展字段
-- 适用于：手动创建表或参考用途
-- 注意：通常gateways表由Alembic迁移自动创建，此脚本仅供参考
-- ====================================

-- 创建gateways表（如果不存在）
CREATE TABLE IF NOT EXISTS gateways (
    id SERIAL PRIMARY KEY,
    vos_instance_id INTEGER NOT NULL,
    vos_uuid UUID,
    
    -- 网关基本信息
    gateway_name VARCHAR(255) NOT NULL,
    gateway_type VARCHAR(50) NOT NULL,
    
    -- 网关配置（基础）
    ip_address VARCHAR(100),
    port INTEGER,
    protocol VARCHAR(50),
    
    -- 在线状态
    is_online BOOLEAN DEFAULT false,
    
    -- 性能指标
    asr DOUBLE PRECISION DEFAULT 0.0,
    acd DOUBLE PRECISION DEFAULT 0.0,
    concurrent_calls INTEGER DEFAULT 0,
    
    -- ========== 扩展字段（从VOS API返回）==========
    
    -- 基础配置
    lock_type INTEGER DEFAULT 0,
    call_level INTEGER DEFAULT 0,
    capacity INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 0,
    gateway_groups TEXT,
    routing_gateway_groups_allow BOOLEAN DEFAULT true,
    routing_gateway_groups TEXT,
    register_type INTEGER DEFAULT 0,
    remote_ips TEXT,
    
    -- 号码检查配置
    caller_e164_check_enable BOOLEAN DEFAULT false,
    caller_e164_check_city BOOLEAN DEFAULT true,
    caller_e164_check_mobile BOOLEAN DEFAULT true,
    caller_e164_check_other BOOLEAN DEFAULT false,
    callee_e164_check_enable BOOLEAN DEFAULT false,
    callee_e164_check_city BOOLEAN DEFAULT true,
    callee_e164_check_mobile BOOLEAN DEFAULT true,
    callee_e164_check_other BOOLEAN DEFAULT false,
    callee_e164_restrict INTEGER DEFAULT 0,
    
    -- RTP和媒体配置
    rtp_forward_type INTEGER DEFAULT 0,
    media_check_direction INTEGER DEFAULT 0,
    max_call_duration_lower INTEGER DEFAULT -1,
    max_call_duration_upper INTEGER DEFAULT -1,
    
    -- 计费配置
    allow_phone_billing BOOLEAN DEFAULT false,
    allow_binded_e164_billing BOOLEAN DEFAULT false,
    enable_phone_setting BOOLEAN DEFAULT false,
    
    -- 限制配置
    deny_same_city_codes_allow BOOLEAN DEFAULT true,
    deny_same_city_codes TEXT,
    check_mobile_area_allow BOOLEAN DEFAULT true,
    check_mobile_area TEXT,
    callout_callee_prefixes_allow BOOLEAN DEFAULT true,
    callout_callee_prefixes TEXT,
    callout_caller_prefixes_allow BOOLEAN DEFAULT true,
    callout_caller_prefixes TEXT,
    
    -- 重写规则
    rewrite_rules_out_callee TEXT,
    rewrite_rules_out_caller TEXT,
    rewrite_rules_in_mobile_area_allow BOOLEAN DEFAULT false,
    rewrite_rules_in_mobile_area TEXT,
    
    -- 超时和SIP配置
    timeout_call_proceeding INTEGER DEFAULT -1,
    sip_response_address_method INTEGER DEFAULT 0,
    sip_request_address_method INTEGER DEFAULT 0,
    
    -- DTMF配置
    dtmf_send_method_h323 INTEGER DEFAULT 0,
    dtmf_send_method_sip INTEGER DEFAULT 0,
    dtmf_receive_method INTEGER DEFAULT 0,
    dtmf_send_payload_type_h323 INTEGER DEFAULT 0,
    dtmf_send_payload_type_sip INTEGER DEFAULT 0,
    dtmf_receive_payload_type INTEGER DEFAULT 0,
    
    -- Q.931配置
    q931_progress_indicator INTEGER DEFAULT -1,
    
    -- 账户信息
    account VARCHAR(255),
    account_name VARCHAR(255),
    password VARCHAR(255),
    customer_password VARCHAR(255),
    
    -- 呼叫失败配置
    call_failed_q931_cause_value TEXT,
    call_failed_sip_code TEXT,
    
    -- SIP域配置
    sip_remote_ring_signal INTEGER DEFAULT 0,
    sip_callee_e164_domain INTEGER DEFAULT 0,
    sip_caller_e164_domain INTEGER DEFAULT 0,
    h323_callee_e164_domain INTEGER DEFAULT 0,
    h323_caller_e164_domain INTEGER DEFAULT 0,
    
    -- 备注
    memo TEXT,
    
    -- SIP认证
    sip_authentication_method INTEGER DEFAULT 0,
    
    -- H.323配置
    h323_fast_start BOOLEAN DEFAULT true,
    h323_h245_tunneling BOOLEAN DEFAULT true,
    h323_h245_in_setup BOOLEAN DEFAULT false,
    h323_auto_call_proceeding BOOLEAN DEFAULT false,
    h323_call_proceeding_from_sip_trying BOOLEAN DEFAULT true,
    h323_alerting_from_sip183_sdp BOOLEAN DEFAULT true,
    h323_t38 BOOLEAN DEFAULT true,
    
    -- SIP高级配置
    sip_timer BOOLEAN DEFAULT true,
    sip_100_rel BOOLEAN DEFAULT true,
    sip_t38 BOOLEAN DEFAULT true,
    sip_display BOOLEAN DEFAULT false,
    sip_remote_party_id BOOLEAN DEFAULT false,
    sip_privacy_support BOOLEAN DEFAULT false,
    
    -- 其他配置
    group_e164_change BOOLEAN DEFAULT false,
    caller_allow_length INTEGER DEFAULT 0,
    callee_allow_length INTEGER DEFAULT 0,
    caller_limit_e164_groups_allow BOOLEAN DEFAULT true,
    caller_limit_e164_groups TEXT,
    callee_limit_e164_groups_allow BOOLEAN DEFAULT true,
    callee_limit_e164_groups TEXT,
    
    -- 利润和费率配置
    min_profit_percent_enable BOOLEAN DEFAULT false,
    min_profit_percent DECIMAL(10, 4) DEFAULT 0.0,
    max_second_rates_enable BOOLEAN DEFAULT false,
    max_second_rates DECIMAL(10, 4) DEFAULT 0.0,
    
    -- 路由策略
    first_route_policy INTEGER DEFAULT 0,
    second_route_policy INTEGER DEFAULT 0,
    
    -- 编解码配置
    h323_g729_send_mode INTEGER DEFAULT 0,
    sip_g729_send_mode INTEGER DEFAULT 0,
    sip_g729_annexb INTEGER DEFAULT 0,
    sip_g723_annexa INTEGER DEFAULT 0,
    h323_codec_assign BOOLEAN DEFAULT false,
    sip_codec_assign BOOLEAN DEFAULT false,
    
    -- RTP和音频配置
    audio_codec_transcoding_enable BOOLEAN DEFAULT false,
    rtp_include_dtmf_inband BOOLEAN DEFAULT false,
    rtp_need_dtmf_inband BOOLEAN DEFAULT false,
    
    -- 其他高级配置
    softswitch_name VARCHAR(255),
    forward_signal_rewrite_e164_group_enable BOOLEAN DEFAULT false,
    forward_signal_rewrite_e164_group TEXT,
    lrn_enable BOOLEAN DEFAULT false,
    lrn_eat_prefix_length INTEGER DEFAULT 0,
    lrn_failure_action INTEGER DEFAULT 0,
    lrn_interstate_billing_prefix TEXT,
    lrn_undetermined_billing_prefix TEXT,
    language VARCHAR(50),
    dynamic_black_list_in_standalone BOOLEAN DEFAULT false,
    media_record BOOLEAN DEFAULT false,
    
    -- 存储完整的VOS原始数据（包括codecs数组等复杂数据）
    raw_data JSONB,
    
    -- 时间戳
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 外键约束
    CONSTRAINT fk_gateways_vos_instance FOREIGN KEY (vos_instance_id) REFERENCES vos_instances(id),
    
    -- 唯一约束
    CONSTRAINT uq_gateway_vos_name UNIQUE (vos_instance_id, gateway_name)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_gateways_id ON gateways(id);
CREATE INDEX IF NOT EXISTS ix_gateways_vos_instance_id ON gateways(vos_instance_id);
CREATE INDEX IF NOT EXISTS ix_gateways_vos_uuid ON gateways(vos_uuid);
CREATE INDEX IF NOT EXISTS ix_gateways_gateway_name ON gateways(gateway_name);
CREATE INDEX IF NOT EXISTS ix_gateways_gateway_type ON gateways(gateway_type);
CREATE INDEX IF NOT EXISTS ix_gateways_is_online ON gateways(is_online);
CREATE INDEX IF NOT EXISTS idx_gateway_vos_name ON gateways(vos_instance_id, gateway_name);
CREATE INDEX IF NOT EXISTS idx_gateway_online ON gateways(vos_instance_id, is_online);
CREATE INDEX IF NOT EXISTS idx_gateway_type ON gateways(vos_instance_id, gateway_type);
CREATE INDEX IF NOT EXISTS idx_gateway_account ON gateways(vos_instance_id, account);

-- 表注释
COMMENT ON TABLE gateways IS 'VOS网关信息表（对接网关 + 落地网关），包含所有配置字段';
COMMENT ON COLUMN gateways.gateway_type IS '网关类型：mapping(对接) 或 routing(落地)';
COMMENT ON COLUMN gateways.raw_data IS '存储完整的VOS API返回数据（JSONB格式），包括codecs数组等复杂数据';

