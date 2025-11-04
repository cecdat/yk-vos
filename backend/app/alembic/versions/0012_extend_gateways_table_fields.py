"""extend gateways table fields

Revision ID: 0012_extend_gateways_fields
Revises: 0011_add_vos_uuid_fields
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0012_extend_gateways_fields'
down_revision = '0011_add_vos_uuid_fields'
branch_labels = None
depends_on = None


def upgrade():
    """为gateways表添加扩展字段"""
    
    # 检查表是否存在
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'gateways' not in inspector.get_table_names():
        # gateways表不存在，跳过字段扩展
        return
    
    # 获取现有列
    columns = [col['name'] for col in inspector.get_columns('gateways')]
    
    # 基础配置字段
    if 'lock_type' not in columns:
        op.add_column('gateways', sa.Column('lock_type', sa.Integer(), server_default='0', nullable=True))
    if 'call_level' not in columns:
        op.add_column('gateways', sa.Column('call_level', sa.Integer(), server_default='0', nullable=True))
    if 'capacity' not in columns:
        op.add_column('gateways', sa.Column('capacity', sa.Integer(), server_default='0', nullable=True))
    if 'priority' not in columns:
        op.add_column('gateways', sa.Column('priority', sa.Integer(), server_default='0', nullable=True))
    if 'gateway_groups' not in columns:
        op.add_column('gateways', sa.Column('gateway_groups', sa.Text(), nullable=True))
    if 'routing_gateway_groups_allow' not in columns:
        op.add_column('gateways', sa.Column('routing_gateway_groups_allow', sa.Boolean(), server_default='true', nullable=True))
    if 'routing_gateway_groups' not in columns:
        op.add_column('gateways', sa.Column('routing_gateway_groups', sa.Text(), nullable=True))
    if 'register_type' not in columns:
        op.add_column('gateways', sa.Column('register_type', sa.Integer(), server_default='0', nullable=True))
    if 'remote_ips' not in columns:
        op.add_column('gateways', sa.Column('remote_ips', sa.Text(), nullable=True))
    
    # 号码检查配置字段
    for field in ['caller_e164_check_enable', 'caller_e164_check_city', 'caller_e164_check_mobile', 'caller_e164_check_other',
                  'callee_e164_check_enable', 'callee_e164_check_city', 'callee_e164_check_mobile', 'callee_e164_check_other']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Boolean(), server_default='false', nullable=True))
    if 'callee_e164_restrict' not in columns:
        op.add_column('gateways', sa.Column('callee_e164_restrict', sa.Integer(), server_default='0', nullable=True))
    
    # RTP和媒体配置字段
    for field in ['rtp_forward_type', 'media_check_direction', 'max_call_duration_lower', 'max_call_duration_upper']:
        if field not in columns:
            default = '-1' if 'duration' in field else '0'
            op.add_column('gateways', sa.Column(field, sa.Integer(), server_default=default, nullable=True))
    
    # 计费配置字段
    for field in ['allow_phone_billing', 'allow_binded_e164_billing', 'enable_phone_setting']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Boolean(), server_default='false', nullable=True))
    
    # 限制配置字段
    if 'deny_same_city_codes_allow' not in columns:
        op.add_column('gateways', sa.Column('deny_same_city_codes_allow', sa.Boolean(), server_default='true', nullable=True))
    for field in ['deny_same_city_codes', 'check_mobile_area', 'callout_callee_prefixes', 'callout_caller_prefixes']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Text(), nullable=True))
    for field in ['check_mobile_area_allow', 'callout_callee_prefixes_allow', 'callout_caller_prefixes_allow']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Boolean(), server_default='true', nullable=True))
    
    # 重写规则字段
    for field in ['rewrite_rules_out_callee', 'rewrite_rules_out_caller', 'rewrite_rules_in_mobile_area']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Text(), nullable=True))
    if 'rewrite_rules_in_mobile_area_allow' not in columns:
        op.add_column('gateways', sa.Column('rewrite_rules_in_mobile_area_allow', sa.Boolean(), server_default='false', nullable=True))
    
    # 超时和SIP配置字段
    for field in ['timeout_call_proceeding', 'sip_response_address_method', 'sip_request_address_method']:
        if field not in columns:
            default = '-1' if 'timeout' in field else '0'
            op.add_column('gateways', sa.Column(field, sa.Integer(), server_default=default, nullable=True))
    
    # DTMF配置字段
    for field in ['dtmf_send_method_h323', 'dtmf_send_method_sip', 'dtmf_receive_method',
                  'dtmf_send_payload_type_h323', 'dtmf_send_payload_type_sip', 'dtmf_receive_payload_type']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Integer(), server_default='0', nullable=True))
    
    # Q.931配置字段
    if 'q931_progress_indicator' not in columns:
        op.add_column('gateways', sa.Column('q931_progress_indicator', sa.Integer(), server_default='-1', nullable=True))
    
    # 账户信息字段
    for field in ['account', 'account_name', 'password', 'customer_password']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.String(255), nullable=True))
    
    # 呼叫失败配置字段
    for field in ['call_failed_q931_cause_value', 'call_failed_sip_code']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Text(), nullable=True))
    
    # SIP域配置字段
    for field in ['sip_remote_ring_signal', 'sip_callee_e164_domain', 'sip_caller_e164_domain',
                  'h323_callee_e164_domain', 'h323_caller_e164_domain']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Integer(), server_default='0', nullable=True))
    
    # 备注字段
    if 'memo' not in columns:
        op.add_column('gateways', sa.Column('memo', sa.Text(), nullable=True))
    
    # SIP认证字段
    if 'sip_authentication_method' not in columns:
        op.add_column('gateways', sa.Column('sip_authentication_method', sa.Integer(), server_default='0', nullable=True))
    
    # H.323配置字段
    for field in ['h323_fast_start', 'h323_h245_tunneling', 'h323_h245_in_setup', 'h323_auto_call_proceeding',
                  'h323_call_proceeding_from_sip_trying', 'h323_alerting_from_sip183_sdp', 'h323_t38']:
        if field not in columns:
            default = 'true' if field in ['h323_fast_start', 'h323_h245_tunneling', 'h323_call_proceeding_from_sip_trying', 'h323_alerting_from_sip183_sdp', 'h323_t38'] else 'false'
            op.add_column('gateways', sa.Column(field, sa.Boolean(), server_default=default, nullable=True))
    
    # SIP高级配置字段
    for field in ['sip_timer', 'sip_100_rel', 'sip_t38', 'sip_display', 'sip_remote_party_id', 'sip_privacy_support']:
        if field not in columns:
            default = 'true' if field in ['sip_timer', 'sip_100_rel', 'sip_t38'] else 'false'
            op.add_column('gateways', sa.Column(field, sa.Boolean(), server_default=default, nullable=True))
    
    # 其他配置字段
    if 'group_e164_change' not in columns:
        op.add_column('gateways', sa.Column('group_e164_change', sa.Boolean(), server_default='false', nullable=True))
    for field in ['caller_allow_length', 'callee_allow_length']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Integer(), server_default='0', nullable=True))
    for field in ['caller_limit_e164_groups_allow', 'callee_limit_e164_groups_allow']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Boolean(), server_default='true', nullable=True))
    for field in ['caller_limit_e164_groups', 'callee_limit_e164_groups']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Text(), nullable=True))
    
    # 利润和费率配置字段
    for field in ['min_profit_percent_enable', 'max_second_rates_enable']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Boolean(), server_default='false', nullable=True))
    for field in ['min_profit_percent', 'max_second_rates']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Float(), server_default='0.0', nullable=True))
    
    # 路由策略字段
    for field in ['first_route_policy', 'second_route_policy']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Integer(), server_default='0', nullable=True))
    
    # 编解码配置字段
    for field in ['h323_g729_send_mode', 'sip_g729_send_mode', 'sip_g729_annexb', 'sip_g723_annexa']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Integer(), server_default='0', nullable=True))
    for field in ['h323_codec_assign', 'sip_codec_assign']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Boolean(), server_default='false', nullable=True))
    
    # RTP和音频配置字段
    for field in ['audio_codec_transcoding_enable', 'rtp_include_dtmf_inband', 'rtp_need_dtmf_inband']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Boolean(), server_default='false', nullable=True))
    
    # 其他高级配置字段
    if 'softswitch_name' not in columns:
        op.add_column('gateways', sa.Column('softswitch_name', sa.String(255), nullable=True))
    if 'forward_signal_rewrite_e164_group_enable' not in columns:
        op.add_column('gateways', sa.Column('forward_signal_rewrite_e164_group_enable', sa.Boolean(), server_default='false', nullable=True))
    if 'forward_signal_rewrite_e164_group' not in columns:
        op.add_column('gateways', sa.Column('forward_signal_rewrite_e164_group', sa.Text(), nullable=True))
    if 'lrn_enable' not in columns:
        op.add_column('gateways', sa.Column('lrn_enable', sa.Boolean(), server_default='false', nullable=True))
    for field in ['lrn_eat_prefix_length', 'lrn_failure_action']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Integer(), server_default='0', nullable=True))
    for field in ['lrn_interstate_billing_prefix', 'lrn_undetermined_billing_prefix']:
        if field not in columns:
            op.add_column('gateways', sa.Column(field, sa.Text(), nullable=True))
    if 'language' not in columns:
        op.add_column('gateways', sa.Column('language', sa.String(50), nullable=True))
    if 'dynamic_black_list_in_standalone' not in columns:
        op.add_column('gateways', sa.Column('dynamic_black_list_in_standalone', sa.Boolean(), server_default='false', nullable=True))
    if 'media_record' not in columns:
        op.add_column('gateways', sa.Column('media_record', sa.Boolean(), server_default='false', nullable=True))
    
    # 添加索引
    try:
        op.create_index('idx_gateway_account', 'gateways', ['vos_instance_id', 'account'], unique=False)
    except Exception:
        pass  # 如果索引已存在则跳过


def downgrade():
    """回滚字段扩展"""
    
    # 删除索引
    try:
        op.drop_index('idx_gateway_account', table_name='gateways')
    except Exception:
        pass
    
    # 删除所有新增字段（按相反顺序删除）
    fields_to_drop = [
        'media_record', 'dynamic_black_list_in_standalone', 'language',
        'lrn_undetermined_billing_prefix', 'lrn_interstate_billing_prefix',
        'lrn_failure_action', 'lrn_eat_prefix_length',
        'forward_signal_rewrite_e164_group', 'forward_signal_rewrite_e164_group_enable',
        'softswitch_name', 'rtp_need_dtmf_inband', 'rtp_include_dtmf_inband',
        'audio_codec_transcoding_enable', 'sip_codec_assign', 'h323_codec_assign',
        'sip_g723_annexa', 'sip_g729_annexb', 'sip_g729_send_mode',
        'h323_g729_send_mode', 'second_route_policy', 'first_route_policy',
        'max_second_rates', 'min_profit_percent', 'max_second_rates_enable',
        'min_profit_percent_enable', 'callee_limit_e164_groups',
        'caller_limit_e164_groups', 'callee_limit_e164_groups_allow',
        'caller_limit_e164_groups_allow', 'callee_allow_length', 'caller_allow_length',
        'group_e164_change', 'sip_privacy_support', 'sip_remote_party_id',
        'sip_display', 'sip_t38', 'sip_100_rel', 'sip_timer',
        'h323_t38', 'h323_alerting_from_sip183_sdp',
        'h323_call_proceeding_from_sip_trying', 'h323_auto_call_proceeding',
        'h323_h245_in_setup', 'h323_h245_tunneling', 'h323_fast_start',
        'sip_authentication_method', 'memo',
        'h323_caller_e164_domain', 'h323_callee_e164_domain',
        'sip_caller_e164_domain', 'sip_callee_e164_domain', 'sip_remote_ring_signal',
        'call_failed_sip_code', 'call_failed_q931_cause_value',
        'customer_password', 'password', 'account_name', 'account',
        'q931_progress_indicator', 'dtmf_receive_payload_type',
        'dtmf_send_payload_type_sip', 'dtmf_send_payload_type_h323',
        'dtmf_receive_method', 'dtmf_send_method_sip', 'dtmf_send_method_h323',
        'sip_request_address_method', 'sip_response_address_method',
        'timeout_call_proceeding', 'rewrite_rules_in_mobile_area',
        'rewrite_rules_in_mobile_area_allow', 'rewrite_rules_out_caller',
        'rewrite_rules_out_callee', 'callout_caller_prefixes',
        'callout_caller_prefixes_allow', 'callout_callee_prefixes',
        'callout_callee_prefixes_allow', 'check_mobile_area',
        'check_mobile_area_allow', 'deny_same_city_codes',
        'deny_same_city_codes_allow', 'enable_phone_setting',
        'allow_binded_e164_billing', 'allow_phone_billing',
        'max_call_duration_upper', 'max_call_duration_lower',
        'media_check_direction', 'rtp_forward_type',
        'callee_e164_restrict', 'callee_e164_check_other',
        'callee_e164_check_mobile', 'callee_e164_check_city',
        'callee_e164_check_enable', 'caller_e164_check_other',
        'caller_e164_check_mobile', 'caller_e164_check_city',
        'caller_e164_check_enable', 'remote_ips', 'register_type',
        'routing_gateway_groups', 'routing_gateway_groups_allow',
        'gateway_groups', 'priority', 'capacity', 'call_level', 'lock_type'
    ]
    
    for field in fields_to_drop:
        try:
            op.drop_column('gateways', field)
        except Exception:
            pass  # 如果字段不存在则跳过

