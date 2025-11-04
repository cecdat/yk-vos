"""Gateway models for VOS gateway data"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from app.models.base import Base


class Gateway(Base):
    """VOS网关信息表（对接网关 + 落地网关）"""
    __tablename__ = 'gateways'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_instance_id = Column(Integer, ForeignKey('vos_instances.id'), nullable=False, index=True)
    vos_uuid = Column(UUID(as_uuid=True), nullable=True, index=True)  # VOS节点唯一标识
    
    # 网关基本信息
    gateway_name = Column(String(255), nullable=False, index=True)  # 网关名称
    gateway_type = Column(String(50), nullable=False, index=True)  # mapping(对接) 或 routing(落地)
    
    # 网关配置（基础）
    ip_address = Column(String(100))  # IP地址
    port = Column(Integer)  # 端口
    protocol = Column(String(50))  # 协议类型
    
    # 在线状态
    is_online = Column(Boolean, default=False, index=True)
    
    # 性能指标
    asr = Column(Float, default=0.0)  # 应答率
    acd = Column(Float, default=0.0)  # 平均通话时长
    concurrent_calls = Column(Integer, default=0)  # 当前并发数
    
    # ========== 扩展字段（从VOS API返回）==========
    
    # 基础配置
    lock_type = Column(Integer, default=0)  # lockType
    call_level = Column(Integer, default=0)  # callLevel
    capacity = Column(Integer, default=0)  # capacity
    priority = Column(Integer, default=0)  # priority
    gateway_groups = Column(Text)  # gatewayGroups
    routing_gateway_groups_allow = Column(Boolean, default=True)  # routingGatewayGroupsAllow
    routing_gateway_groups = Column(Text)  # routingGatewayGroups
    register_type = Column(Integer, default=0)  # registerType
    remote_ips = Column(Text)  # remoteIps (IP列表，逗号分隔)
    
    # 号码检查配置
    caller_e164_check_enable = Column(Boolean, default=False)  # callerE164CheckEnable
    caller_e164_check_city = Column(Boolean, default=True)  # callerE164CheckCity
    caller_e164_check_mobile = Column(Boolean, default=True)  # callerE164CheckMobile
    caller_e164_check_other = Column(Boolean, default=False)  # callerE164CheckOther
    callee_e164_check_enable = Column(Boolean, default=False)  # calleeE164CheckEnable
    callee_e164_check_city = Column(Boolean, default=True)  # calleeE164CheckCity
    callee_e164_check_mobile = Column(Boolean, default=True)  # calleeE164CheckMobile
    callee_e164_check_other = Column(Boolean, default=False)  # calleeE164CheckOther
    callee_e164_restrict = Column(Integer, default=0)  # calleeE164Restrict
    
    # RTP和媒体配置
    rtp_forward_type = Column(Integer, default=0)  # rtpForwardType
    media_check_direction = Column(Integer, default=0)  # mediaCheckDirection
    max_call_duration_lower = Column(Integer, default=-1)  # maxCallDurationLower
    max_call_duration_upper = Column(Integer, default=-1)  # maxCallDurationUpper
    
    # 计费配置
    allow_phone_billing = Column(Boolean, default=False)  # allowPhoneBilling
    allow_binded_e164_billing = Column(Boolean, default=False)  # allowBindedE164Billing
    enable_phone_setting = Column(Boolean, default=False)  # enablePhoneSetting
    
    # 限制配置
    deny_same_city_codes_allow = Column(Boolean, default=True)  # denySameCityCodesAllow
    deny_same_city_codes = Column(Text)  # denySameCityCodes
    check_mobile_area_allow = Column(Boolean, default=True)  # checkMobileAreaAllow
    check_mobile_area = Column(Text)  # checkMobileArea
    callout_callee_prefixes_allow = Column(Boolean, default=True)  # calloutCalleePrefixesAllow
    callout_callee_prefixes = Column(Text)  # calloutCalleePrefixes
    callout_caller_prefixes_allow = Column(Boolean, default=True)  # calloutCallerPrefixesAllow
    callout_caller_prefixes = Column(Text)  # calloutCallerPrefixes
    
    # 重写规则
    rewrite_rules_out_callee = Column(Text)  # rewriteRulesOutCallee
    rewrite_rules_out_caller = Column(Text)  # rewriteRulesOutCaller
    rewrite_rules_in_mobile_area_allow = Column(Boolean, default=False)  # rewriteRulesInMobileAreaAllow
    rewrite_rules_in_mobile_area = Column(Text)  # rewriteRulesInMobileArea
    
    # 超时和SIP配置
    timeout_call_proceeding = Column(Integer, default=-1)  # timeoutCallProceeding
    sip_response_address_method = Column(Integer, default=0)  # sipResponseAddressMethod
    sip_request_address_method = Column(Integer, default=0)  # sipRequestAddressMethod
    
    # DTMF配置
    dtmf_send_method_h323 = Column(Integer, default=0)  # dtmfSendMethodH323
    dtmf_send_method_sip = Column(Integer, default=0)  # dtmfSendMethodSip
    dtmf_receive_method = Column(Integer, default=0)  # dtmfReceiveMethod
    dtmf_send_payload_type_h323 = Column(Integer, default=0)  # dtmfSendPayloadTypeH323
    dtmf_send_payload_type_sip = Column(Integer, default=0)  # dtmfSendPayloadTypeSip
    dtmf_receive_payload_type = Column(Integer, default=0)  # dtmfReceivePayloadType
    
    # Q.931配置
    q931_progress_indicator = Column(Integer, default=-1)  # q931ProgressIndicator
    
    # 账户信息
    account = Column(String(255))  # account
    account_name = Column(String(255))  # accountName
    password = Column(String(255))  # password (敏感信息，但VOS返回了)
    customer_password = Column(String(255))  # customerPassword
    
    # 呼叫失败配置
    call_failed_q931_cause_value = Column(Text)  # callFailedQ931CauseValue
    call_failed_sip_code = Column(Text)  # callFailedSipCode
    
    # SIP域配置
    sip_remote_ring_signal = Column(Integer, default=0)  # sipRemoteRingSignal
    sip_callee_e164_domain = Column(Integer, default=0)  # sipCalleeE164Domain
    sip_caller_e164_domain = Column(Integer, default=0)  # sipCallerE164Domain
    h323_callee_e164_domain = Column(Integer, default=0)  # h323CalleeE164Domain
    h323_caller_e164_domain = Column(Integer, default=0)  # h323CallerE164Domain
    
    # 备注
    memo = Column(Text)  # memo
    
    # SIP认证
    sip_authentication_method = Column(Integer, default=0)  # sipAuthenticationMethod
    
    # H.323配置
    h323_fast_start = Column(Boolean, default=True)  # h323FastStart
    h323_h245_tunneling = Column(Boolean, default=True)  # h323H245Tunneling
    h323_h245_in_setup = Column(Boolean, default=False)  # h323H245InSetup
    h323_auto_call_proceeding = Column(Boolean, default=False)  # h323AutoCallProceeding
    h323_call_proceeding_from_sip_trying = Column(Boolean, default=True)  # h323CallProceedingFromSipTrying
    h323_alerting_from_sip183_sdp = Column(Boolean, default=True)  # h323AlertingFromSip183Sdp
    h323_t38 = Column(Boolean, default=True)  # h323T38
    
    # SIP高级配置
    sip_timer = Column(Boolean, default=True)  # sipTimer
    sip_100_rel = Column(Boolean, default=True)  # sip100Rel
    sip_t38 = Column(Boolean, default=True)  # sipT38
    sip_display = Column(Boolean, default=False)  # sipDisplay
    sip_remote_party_id = Column(Boolean, default=False)  # sipRemotePartyId
    sip_privacy_support = Column(Boolean, default=False)  # sipPrivacySupport
    
    # 其他配置
    group_e164_change = Column(Boolean, default=False)  # groupE164Change
    caller_allow_length = Column(Integer, default=0)  # callerAllowLength
    callee_allow_length = Column(Integer, default=0)  # calleeAllowLength
    caller_limit_e164_groups_allow = Column(Boolean, default=True)  # callerLimitE164GroupsAllow
    caller_limit_e164_groups = Column(Text)  # callerLimitE164Groups
    callee_limit_e164_groups_allow = Column(Boolean, default=True)  # calleeLimitE164GroupsAllow
    callee_limit_e164_groups = Column(Text)  # calleeLimitE164Groups
    
    # 利润和费率配置
    min_profit_percent_enable = Column(Boolean, default=False)  # minProfitPercentEnable
    min_profit_percent = Column(Float, default=0.0)  # minProfitPercent
    max_second_rates_enable = Column(Boolean, default=False)  # maxSecondRatesEnable
    max_second_rates = Column(Float, default=0.0)  # maxSecondRates
    
    # 路由策略
    first_route_policy = Column(Integer, default=0)  # firstRoutePolicy
    second_route_policy = Column(Integer, default=0)  # secondRoutePolicy
    
    # 编解码配置
    h323_g729_send_mode = Column(Integer, default=0)  # h323G729SendMode
    sip_g729_send_mode = Column(Integer, default=0)  # sipG729SendMode
    sip_g729_annexb = Column(Integer, default=0)  # sipG729Annexb
    sip_g723_annexa = Column(Integer, default=0)  # sipG723Annexa
    h323_codec_assign = Column(Boolean, default=False)  # h323CodecAssign
    sip_codec_assign = Column(Boolean, default=False)  # sipCodecAssign
    
    # RTP和音频配置
    audio_codec_transcoding_enable = Column(Boolean, default=False)  # audioCodecTranscodingEnable
    rtp_include_dtmf_inband = Column(Boolean, default=False)  # rtpIncludeDtmfInband
    rtp_need_dtmf_inband = Column(Boolean, default=False)  # rtpNeedDtmfInband
    
    # 其他高级配置
    softswitch_name = Column(String(255))  # softswitchName
    forward_signal_rewrite_e164_group_enable = Column(Boolean, default=False)  # forwardSignalRewriteE164GroupEnable
    forward_signal_rewrite_e164_group = Column(Text)  # forwardSignalRewriteE164Group
    lrn_enable = Column(Boolean, default=False)  # lrnEnable
    lrn_eat_prefix_length = Column(Integer, default=0)  # lrnEatPrefixLength
    lrn_failure_action = Column(Integer, default=0)  # lrnFailureAction
    lrn_interstate_billing_prefix = Column(Text)  # lrnInterstateBillingPrefix
    lrn_undetermined_billing_prefix = Column(Text)  # lrnUndeterminedBillingPrefix
    language = Column(String(50))  # language
    dynamic_black_list_in_standalone = Column(Boolean, default=False)  # dynamicBlackListInStandalone
    media_record = Column(Boolean, default=False)  # mediaRecord
    
    # 存储完整的VOS原始数据（包括codecs数组等复杂数据）
    raw_data = Column(JSONB, nullable=True)
    
    # 时间戳
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 复合索引
    __table_args__ = (
        Index('idx_gateway_vos_name', 'vos_instance_id', 'gateway_name', unique=True),
        Index('idx_gateway_online', 'vos_instance_id', 'is_online'),
        Index('idx_gateway_type', 'vos_instance_id', 'gateway_type'),
        Index('idx_gateway_account', 'vos_instance_id', 'account'),
    )
    
    def __repr__(self):
        return f"<Gateway {self.gateway_name} ({self.gateway_type})>"


class FeeRateGroup(Base):
    """费率组表"""
    __tablename__ = 'fee_rate_groups'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_instance_id = Column(Integer, ForeignKey('vos_instances.id'), nullable=False, index=True)
    
    # 费率组信息
    group_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # 存储完整配置
    raw_data = Column(JSONB, nullable=True)
    
    # 时间戳
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_feerate_vos_name', 'vos_instance_id', 'group_name', unique=True),
    )
    
    def __repr__(self):
        return f"<FeeRateGroup {self.group_name}>"


class Suite(Base):
    """套餐表"""
    __tablename__ = 'suites'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_instance_id = Column(Integer, ForeignKey('vos_instances.id'), nullable=False, index=True)
    
    # 套餐信息
    suite_id = Column(String(100), nullable=False, index=True)  # VOS中的套餐ID
    suite_name = Column(String(255))
    suite_type = Column(String(100))
    
    # 费用信息
    price = Column(Float, default=0.0)
    monthly_fee = Column(Float, default=0.0)
    
    # 套餐内容
    duration = Column(Integer, default=0)  # 时长（分钟）
    
    # 存储完整配置
    raw_data = Column(JSONB, nullable=True)
    
    # 时间戳
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_suite_vos_id', 'vos_instance_id', 'suite_id', unique=True),
    )
    
    def __repr__(self):
        return f"<Suite {self.suite_name}>"

