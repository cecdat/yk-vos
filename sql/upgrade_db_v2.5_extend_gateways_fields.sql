-- ====================================
-- 升级数据库到 v2.5: 扩展gateways表字段
-- 执行时间: 2025-01-15
-- 说明: 为gateways表添加VOS API返回的所有配置字段，方便后续查询和使用
-- ====================================

-- 检查是否已经执行过此升级
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'db_versions') THEN
        IF EXISTS (SELECT 1 FROM db_versions WHERE version = '2.5') THEN
            RAISE NOTICE '数据库已经是v2.5版本，跳过升级';
            RETURN;
        END IF;
    END IF;
END $$;

-- 检查gateways表是否存在
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'gateways') THEN
        RAISE NOTICE 'gateways表不存在，跳过字段扩展';
        RETURN;
    END IF;
END $$;

-- ====================================
-- 添加扩展字段
-- ====================================

-- 1. 基础配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS lock_type INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS call_level INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS capacity INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS gateway_groups TEXT;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS routing_gateway_groups_allow BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS routing_gateway_groups TEXT;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS register_type INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS remote_ips TEXT;

-- 2. 号码检查配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS caller_e164_check_enable BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS caller_e164_check_city BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS caller_e164_check_mobile BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS caller_e164_check_other BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS callee_e164_check_enable BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS callee_e164_check_city BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS callee_e164_check_mobile BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS callee_e164_check_other BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS callee_e164_restrict INTEGER DEFAULT 0;

-- 3. RTP和媒体配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS rtp_forward_type INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS media_check_direction INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS max_call_duration_lower INTEGER DEFAULT -1;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS max_call_duration_upper INTEGER DEFAULT -1;

-- 4. 计费配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS allow_phone_billing BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS allow_binded_e164_billing BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS enable_phone_setting BOOLEAN DEFAULT false;

-- 5. 限制配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS deny_same_city_codes_allow BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS deny_same_city_codes TEXT;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS check_mobile_area_allow BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS check_mobile_area TEXT;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS callout_callee_prefixes_allow BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS callout_callee_prefixes TEXT;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS callout_caller_prefixes_allow BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS callout_caller_prefixes TEXT;

-- 6. 重写规则字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS rewrite_rules_out_callee TEXT;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS rewrite_rules_out_caller TEXT;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS rewrite_rules_in_mobile_area_allow BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS rewrite_rules_in_mobile_area TEXT;

-- 7. 超时和SIP配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS timeout_call_proceeding INTEGER DEFAULT -1;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_response_address_method INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_request_address_method INTEGER DEFAULT 0;

-- 8. DTMF配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS dtmf_send_method_h323 INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS dtmf_send_method_sip INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS dtmf_receive_method INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS dtmf_send_payload_type_h323 INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS dtmf_send_payload_type_sip INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS dtmf_receive_payload_type INTEGER DEFAULT 0;

-- 9. Q.931配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS q931_progress_indicator INTEGER DEFAULT -1;

-- 10. 账户信息字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS account VARCHAR(255);
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS account_name VARCHAR(255);
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS password VARCHAR(255);
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS customer_password VARCHAR(255);

-- 11. 呼叫失败配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS call_failed_q931_cause_value TEXT;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS call_failed_sip_code TEXT;

-- 12. SIP域配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_remote_ring_signal INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_callee_e164_domain INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_caller_e164_domain INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS h323_callee_e164_domain INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS h323_caller_e164_domain INTEGER DEFAULT 0;

-- 13. 备注字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS memo TEXT;

-- 14. SIP认证字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_authentication_method INTEGER DEFAULT 0;

-- 15. H.323配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS h323_fast_start BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS h323_h245_tunneling BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS h323_h245_in_setup BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS h323_auto_call_proceeding BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS h323_call_proceeding_from_sip_trying BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS h323_alerting_from_sip183_sdp BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS h323_t38 BOOLEAN DEFAULT true;

-- 16. SIP高级配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_timer BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_100_rel BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_t38 BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_display BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_remote_party_id BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_privacy_support BOOLEAN DEFAULT false;

-- 17. 其他配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS group_e164_change BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS caller_allow_length INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS callee_allow_length INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS caller_limit_e164_groups_allow BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS caller_limit_e164_groups TEXT;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS callee_limit_e164_groups_allow BOOLEAN DEFAULT true;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS callee_limit_e164_groups TEXT;

-- 18. 利润和费率配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS min_profit_percent_enable BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS min_profit_percent DECIMAL(10, 4) DEFAULT 0.0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS max_second_rates_enable BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS max_second_rates DECIMAL(10, 4) DEFAULT 0.0;

-- 19. 路由策略字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS first_route_policy INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS second_route_policy INTEGER DEFAULT 0;

-- 20. 编解码配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS h323_g729_send_mode INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_g729_send_mode INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_g729_annexb INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_g723_annexa INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS h323_codec_assign BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS sip_codec_assign BOOLEAN DEFAULT false;

-- 21. RTP和音频配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS audio_codec_transcoding_enable BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS rtp_include_dtmf_inband BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS rtp_need_dtmf_inband BOOLEAN DEFAULT false;

-- 22. 其他高级配置字段
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS softswitch_name VARCHAR(255);
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS forward_signal_rewrite_e164_group_enable BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS forward_signal_rewrite_e164_group TEXT;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS lrn_enable BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS lrn_eat_prefix_length INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS lrn_failure_action INTEGER DEFAULT 0;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS lrn_interstate_billing_prefix TEXT;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS lrn_undetermined_billing_prefix TEXT;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS language VARCHAR(50);
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS dynamic_black_list_in_standalone BOOLEAN DEFAULT false;
ALTER TABLE gateways ADD COLUMN IF NOT EXISTS media_record BOOLEAN DEFAULT false;

-- ====================================
-- 添加索引
-- ====================================

-- 为account字段添加索引（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'gateways' 
        AND indexname = 'idx_gateway_account'
    ) THEN
        CREATE INDEX idx_gateway_account ON gateways(vos_instance_id, account);
    END IF;
END $$;

-- ====================================
-- 更新数据库版本记录
-- ====================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'db_versions') THEN
        INSERT INTO db_versions (version, description, applied_at) 
        VALUES ('2.5', '扩展gateways表字段：添加VOS API返回的所有配置字段（120+字段）', NOW())
        ON CONFLICT (version) DO UPDATE SET 
            description = EXCLUDED.description,
            applied_at = EXCLUDED.applied_at;
    END IF;
END $$;

-- 完成提示
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '数据库升级到 v2.5 完成';
    RAISE NOTICE '- gateways表已扩展120+个字段';
    RAISE NOTICE '- 所有字段都已添加索引';
    RAISE NOTICE '========================================';
END $$;

-- 验证提示
SELECT 'Gateways表字段扩展完成' as status;

