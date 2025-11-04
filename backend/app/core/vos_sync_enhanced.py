"""
增强版 VOS 数据同步服务
实现双写策略：专门表 + 通用缓存
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.phone_enhanced import PhoneEnhanced
from app.models.gateway import Gateway, FeeRateGroup, Suite
from app.models.customer import Customer
from app.models.vos_instance import VOSInstance
from app.core.vos_client import VOSClient
from app.core.vos_cache_service import VosCacheService

logger = logging.getLogger(__name__)


class VosSyncEnhanced:
    """增强版 VOS 同步服务"""
    
    def __init__(self, db: Session, vos_instance_id: int, base_url: str):
        self.db = db
        self.vos_instance_id = vos_instance_id
        self.client = VOSClient(base_url)
        self.cache_service = VosCacheService(db)
        # 获取VOS实例信息（用于获取vos_uuid）
        self.vos_instance = db.query(VOSInstance).filter(VOSInstance.id == vos_instance_id).first()
    
    # ==================== 话机同步（增强版）====================
    
    def sync_phones_online(self) -> Dict[str, Any]:
        """
        同步在线话机
        双写：phones_enhanced + vos_data_cache
        """
        logger.info(f"开始同步在线话机 (instance={self.vos_instance_id})")
        
        try:
            # 调用 VOS API
            result = self.client.call_api('/external/server/GetAllPhoneOnline', {})
            
            if not self.client.is_success(result):
                error_msg = self.client.get_error_message(result)
                logger.error(f"获取在线话机失败: {error_msg}")
                return {'success': False, 'error': error_msg}
            
            # 解析话机数据
            phones_data = result.get('infoPhoneOnlines', [])
            if not isinstance(phones_data, list):
                phones_data = []
            
            # 1. 将所有话机标记为离线
            self.db.query(PhoneEnhanced).filter(
                PhoneEnhanced.vos_instance_id == self.vos_instance_id
            ).update({'is_online': False})
            
            # 2. 更新在线话机到专门表
            online_count = 0
            for phone_data in phones_data:
                e164 = phone_data.get('e164') or phone_data.get('E164')
                if not e164:
                    continue
                
                # 查找或创建话机记录
                phone = self.db.query(PhoneEnhanced).filter(
                    and_(
                        PhoneEnhanced.vos_instance_id == self.vos_instance_id,
                        PhoneEnhanced.e164 == e164
                    )
                ).first()
                
                if phone:
                    # 更新现有记录
                    phone.is_online = True
                    phone.last_seen = datetime.utcnow()
                    phone.ip_address = phone_data.get('ipAddress') or phone_data.get('ip')
                    phone.port = phone_data.get('port')
                    phone.raw_data = phone_data
                    phone.synced_at = datetime.utcnow()
                else:
                    # 创建新记录
                    phone = PhoneEnhanced(
                        vos_instance_id=self.vos_instance_id,
                        e164=e164,
                        account=phone_data.get('account'),
                        is_online=True,
                        register_time=datetime.utcnow(),
                        last_seen=datetime.utcnow(),
                        ip_address=phone_data.get('ipAddress') or phone_data.get('ip'),
                        port=phone_data.get('port'),
                        user_agent=phone_data.get('userAgent'),
                        raw_data=phone_data
                    )
                    self.db.add(phone)
                
                online_count += 1
            
            self.db.commit()
            
            # 3. 同时更新通用缓存
            self.cache_service._save_to_cache(
                vos_instance_id=self.vos_instance_id,
                api_path='/external/server/GetAllPhoneOnline',
                cache_key=VosCacheService.generate_cache_key('/external/server/GetAllPhoneOnline', {}),
                params={},
                response_data=result,
                is_valid=True,
                ret_code=0,
                error_message=None
            )
            
            logger.info(f"在线话机同步完成: {online_count} 部在线")
            return {
                'success': True,
                'online_count': online_count,
                'total_phones': len(phones_data)
            }
            
        except Exception as e:
            logger.exception(f"同步在线话机失败: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    # ==================== 网关同步（新增）====================
    
    def sync_gateways(self, gateway_type: str = 'both') -> Dict[str, Any]:
        """
        同步网关信息
        gateway_type: 'mapping'(对接) / 'routing'(落地) / 'both'(全部)
        """
        logger.info(f"开始同步网关 (instance={self.vos_instance_id}, type={gateway_type})")
        
        results = {'mapping': None, 'routing': None}
        has_error = False
        error_messages = []
        
        try:
            # 同步对接网关
            if gateway_type in ['mapping', 'both']:
                logger.info(f"同步对接网关 (instance={self.vos_instance_id})")
                mapping_result = self._sync_gateway_type('mapping')
                results['mapping'] = mapping_result
                if not mapping_result.get('success', False):
                    has_error = True
                    error_msg = mapping_result.get('error', '未知错误')
                    error_messages.append(f"对接网关同步失败: {error_msg}")
                    logger.error(f"对接网关同步失败 (instance={self.vos_instance_id}): {error_msg}")
                else:
                    logger.info(f"对接网关同步成功 (instance={self.vos_instance_id}): {mapping_result.get('count', 0)} 个")
            
            # 同步落地网关
            if gateway_type in ['routing', 'both']:
                logger.info(f"同步落地网关 (instance={self.vos_instance_id})")
                routing_result = self._sync_gateway_type('routing')
                results['routing'] = routing_result
                if not routing_result.get('success', False):
                    has_error = True
                    error_msg = routing_result.get('error', '未知错误')
                    error_messages.append(f"落地网关同步失败: {error_msg}")
                    logger.error(f"落地网关同步失败 (instance={self.vos_instance_id}): {error_msg}")
                else:
                    logger.info(f"落地网关同步成功 (instance={self.vos_instance_id}): {routing_result.get('count', 0)} 个")
            
            # 汇总结果
            total_count = 0
            if results['mapping'] and results['mapping'].get('success'):
                total_count += results['mapping'].get('count', 0)
            if results['routing'] and results['routing'].get('success'):
                total_count += results['routing'].get('count', 0)
            
            if has_error:
                logger.warning(f"网关同步部分失败 (instance={self.vos_instance_id}): {'; '.join(error_messages)}")
                return {
                    'success': False,
                    'error': '; '.join(error_messages),
                    'results': results,
                    'total_count': total_count
                }
            else:
                logger.info(f"网关同步完成 (instance={self.vos_instance_id}): 共 {total_count} 个网关")
                return {
                    'success': True,
                    'results': results,
                    'total_count': total_count
                }
            
        except Exception as e:
            logger.exception(f"同步网关失败: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e), 'results': results}
    
    def _map_gateway_fields(self, gw_data: Dict[str, Any], online_info: Dict[str, Any], is_online: bool, gw_type: str) -> Dict[str, Any]:
        """
        将VOS API返回的字段映射到Gateway模型的字段
        """
        # 字段映射表：{VOS API字段名: Gateway模型字段名}
        field_mapping = {
            # 基础配置
            'lockType': ('lock_type', int),
            'callLevel': ('call_level', int),
            'capacity': ('capacity', int),
            'priority': ('priority', int),
            'gatewayGroups': ('gateway_groups', str),
            'routingGatewayGroupsAllow': ('routing_gateway_groups_allow', bool),
            'routingGatewayGroups': ('routing_gateway_groups', str),
            'registerType': ('register_type', int),
            'remoteIps': ('remote_ips', str),
            
            # 号码检查配置
            'callerE164CheckEnable': ('caller_e164_check_enable', bool),
            'callerE164CheckCity': ('caller_e164_check_city', bool),
            'callerE164CheckMobile': ('caller_e164_check_mobile', bool),
            'callerE164CheckOther': ('caller_e164_check_other', bool),
            'calleeE164CheckEnable': ('callee_e164_check_enable', bool),
            'calleeE164CheckCity': ('callee_e164_check_city', bool),
            'calleeE164CheckMobile': ('callee_e164_check_mobile', bool),
            'calleeE164CheckOther': ('callee_e164_check_other', bool),
            'calleeE164Restrict': ('callee_e164_restrict', int),
            
            # RTP和媒体配置
            'rtpForwardType': ('rtp_forward_type', int),
            'mediaCheckDirection': ('media_check_direction', int),
            'maxCallDurationLower': ('max_call_duration_lower', int),
            'maxCallDurationUpper': ('max_call_duration_upper', int),
            
            # 计费配置
            'allowPhoneBilling': ('allow_phone_billing', bool),
            'allowBindedE164Billing': ('allow_binded_e164_billing', bool),
            'enablePhoneSetting': ('enable_phone_setting', bool),
            
            # 限制配置
            'denySameCityCodesAllow': ('deny_same_city_codes_allow', bool),
            'denySameCityCodes': ('deny_same_city_codes', str),
            'checkMobileAreaAllow': ('check_mobile_area_allow', bool),
            'checkMobileArea': ('check_mobile_area', str),
            'calloutCalleePrefixesAllow': ('callout_callee_prefixes_allow', bool),
            'calloutCalleePrefixes': ('callout_callee_prefixes', str),
            'calloutCallerPrefixesAllow': ('callout_caller_prefixes_allow', bool),
            'calloutCallerPrefixes': ('callout_caller_prefixes', str),
            
            # 重写规则
            'rewriteRulesOutCallee': ('rewrite_rules_out_callee', str),
            'rewriteRulesOutCaller': ('rewrite_rules_out_caller', str),
            'rewriteRulesInMobileAreaAllow': ('rewrite_rules_in_mobile_area_allow', bool),
            'rewriteRulesInMobileArea': ('rewrite_rules_in_mobile_area', str),
            
            # 超时和SIP配置
            'timeoutCallProceeding': ('timeout_call_proceeding', int),
            'sipResponseAddressMethod': ('sip_response_address_method', int),
            'sipRequestAddressMethod': ('sip_request_address_method', int),
            
            # DTMF配置
            'dtmfSendMethodH323': ('dtmf_send_method_h323', int),
            'dtmfSendMethodSip': ('dtmf_send_method_sip', int),
            'dtmfReceiveMethod': ('dtmf_receive_method', int),
            'dtmfSendPayloadTypeH323': ('dtmf_send_payload_type_h323', int),
            'dtmfSendPayloadTypeSip': ('dtmf_send_payload_type_sip', int),
            'dtmfReceivePayloadType': ('dtmf_receive_payload_type', int),
            
            # Q.931配置
            'q931ProgressIndicator': ('q931_progress_indicator', int),
            
            # 账户信息
            'account': ('account', str),
            'accountName': ('account_name', str),
            'password': ('password', str),
            'customerPassword': ('customer_password', str),
            
            # 呼叫失败配置
            'callFailedQ931CauseValue': ('call_failed_q931_cause_value', str),
            'callFailedSipCode': ('call_failed_sip_code', str),
            
            # SIP域配置
            'sipRemoteRingSignal': ('sip_remote_ring_signal', int),
            'sipCalleeE164Domain': ('sip_callee_e164_domain', int),
            'sipCallerE164Domain': ('sip_caller_e164_domain', int),
            'h323CalleeE164Domain': ('h323_callee_e164_domain', int),
            'h323CallerE164Domain': ('h323_caller_e164_domain', int),
            
            # 备注
            'memo': ('memo', str),
            
            # SIP认证
            'sipAuthenticationMethod': ('sip_authentication_method', int),
            
            # H.323配置
            'h323FastStart': ('h323_fast_start', bool),
            'h323H245Tunneling': ('h323_h245_tunneling', bool),
            'h323H245InSetup': ('h323_h245_in_setup', bool),
            'h323AutoCallProceeding': ('h323_auto_call_proceeding', bool),
            'h323CallProceedingFromSipTrying': ('h323_call_proceeding_from_sip_trying', bool),
            'h323AlertingFromSip183Sdp': ('h323_alerting_from_sip183_sdp', bool),
            'h323T38': ('h323_t38', bool),
            
            # SIP高级配置
            'sipTimer': ('sip_timer', bool),
            'sip100Rel': ('sip_100_rel', bool),
            'sipT38': ('sip_t38', bool),
            'sipDisplay': ('sip_display', bool),
            'sipRemotePartyId': ('sip_remote_party_id', bool),
            'sipPrivacySupport': ('sip_privacy_support', bool),
            
            # 其他配置
            'groupE164Change': ('group_e164_change', bool),
            'callerAllowLength': ('caller_allow_length', int),
            'calleeAllowLength': ('callee_allow_length', int),
            'callerLimitE164GroupsAllow': ('caller_limit_e164_groups_allow', bool),
            'callerLimitE164Groups': ('caller_limit_e164_groups', str),
            'calleeLimitE164GroupsAllow': ('callee_limit_e164_groups_allow', bool),
            'calleeLimitE164Groups': ('callee_limit_e164_groups', str),
            
            # 利润和费率配置
            'minProfitPercentEnable': ('min_profit_percent_enable', bool),
            'minProfitPercent': ('min_profit_percent', float),
            'maxSecondRatesEnable': ('max_second_rates_enable', bool),
            'maxSecondRates': ('max_second_rates', float),
            
            # 路由策略
            'firstRoutePolicy': ('first_route_policy', int),
            'secondRoutePolicy': ('second_route_policy', int),
            
            # 编解码配置
            'h323G729SendMode': ('h323_g729_send_mode', int),
            'sipG729SendMode': ('sip_g729_send_mode', int),
            'sipG729Annexb': ('sip_g729_annexb', int),
            'sipG723Annexa': ('sip_g723_annexa', int),
            'h323CodecAssign': ('h323_codec_assign', bool),
            'sipCodecAssign': ('sip_codec_assign', bool),
            
            # RTP和音频配置
            'audioCodecTranscodingEnable': ('audio_codec_transcoding_enable', bool),
            'rtpIncludeDtmfInband': ('rtp_include_dtmf_inband', bool),
            'rtpNeedDtmfInband': ('rtp_need_dtmf_inband', bool),
            
            # 其他高级配置
            'softswitchName': ('softswitch_name', str),
            'forwardSignalRewriteE164GroupEnable': ('forward_signal_rewrite_e164_group_enable', bool),
            'forwardSignalRewriteE164Group': ('forward_signal_rewrite_e164_group', str),
            'lrnEnable': ('lrn_enable', bool),
            'lrnEatPrefixLength': ('lrn_eat_prefix_length', int),
            'lrnFailureAction': ('lrn_failure_action', int),
            'lrnInterstateBillingPrefix': ('lrn_interstate_billing_prefix', str),
            'lrnUndeterminedBillingPrefix': ('lrn_undetermined_billing_prefix', str),
            'language': ('language', str),
            'dynamicBlackListInStandalone': ('dynamic_black_list_in_standalone', bool),
            'mediaRecord': ('media_record', bool),
        }
        
        result = {
            # 基础字段
            'gateway_name': gw_data.get('name', ''),
            'gateway_type': gw_type,
            'is_online': is_online,
            'ip_address': gw_data.get('ipAddress') or gw_data.get('ip'),
            'port': gw_data.get('port'),
            'protocol': gw_data.get('protocol'),
            'asr': online_info.get('asr', 0.0),
            'acd': online_info.get('acd', 0.0),
            'concurrent_calls': online_info.get('concurrentCalls', 0),
        }
        
        # 映射所有字段
        for vos_key, (model_key, data_type) in field_mapping.items():
            value = gw_data.get(vos_key)
            if value is not None:
                try:
                    # 类型转换
                    if data_type == int:
                        result[model_key] = int(value) if value != '' else 0
                    elif data_type == float:
                        result[model_key] = float(value) if value != '' else 0.0
                    elif data_type == bool:
                        result[model_key] = bool(value) if isinstance(value, bool) else (value == 'true' or value == True)
                    elif data_type == str:
                        result[model_key] = str(value) if value is not None else ''
                    else:
                        result[model_key] = value
                except (ValueError, TypeError) as e:
                    logger.warning(f"字段映射失败 {vos_key} -> {model_key}: {e}, 值={value}")
                    # 使用默认值
                    if data_type == int:
                        result[model_key] = 0
                    elif data_type == float:
                        result[model_key] = 0.0
                    elif data_type == bool:
                        result[model_key] = False
                    elif data_type == str:
                        result[model_key] = ''
        
        return result
    
    def _sync_gateway_type(self, gw_type: str) -> Dict[str, Any]:
        """同步特定类型的网关"""
        api_path = f'/external/server/GetGateway{"Mapping" if gw_type == "mapping" else "Routing"}'
        api_path_online = f'{api_path}Online'
        
        # 1. 获取网关配置
        config_result = self.client.call_api(api_path, {})
        if not self.client.is_success(config_result):
            return {'success': False, 'error': self.client.get_error_message(config_result)}
        
        # 2. 获取在线状态
        online_result = self.client.call_api(api_path_online, {})
        online_data = {}
        if self.client.is_success(online_result):
            online_list = online_result.get('infoGatewayMappingsOnline' if gw_type == 'mapping' else 'infoGatewayRoutingsOnline', [])
            for gw in online_list:
                name = gw.get('name')
                if name:
                    online_data[name] = gw
        
        # 3. 更新到专门表
        gateways_list = config_result.get('infoGatewayMappings' if gw_type == 'mapping' else 'infoGatewayRoutings', [])
        if not isinstance(gateways_list, list):
            logger.warning(f"网关列表格式异常 (type={gw_type}, instance={self.vos_instance_id}): {type(gateways_list)}")
            gateways_list = []
        
        logger.info(f"获取到 {len(gateways_list)} 个{gw_type}网关配置 (instance={self.vos_instance_id})")
        synced_count = 0
        
        if len(gateways_list) == 0:
            logger.info(f"VOS实例 {self.vos_instance_id} 没有配置{gw_type}网关，跳过同步")
            # 即使没有网关，也返回成功（这是正常情况）
            return {'success': True, 'count': 0, 'message': f'没有配置{gw_type}网关'}
        
        for gw_data in gateways_list:
            gateway_name = gw_data.get('name')
            if not gateway_name:
                continue
            
            # 获取在线状态和性能数据
            online_info = online_data.get(gateway_name, {})
            is_online = online_info.get('isOnline', False) or online_info.get('online', False)
            
            # 合并所有数据：优先使用在线数据，然后是配置数据
            # 确保保存完整的网关配置信息
            merged_data = gw_data.copy()  # 先复制配置数据
            merged_data.update(online_info)  # 然后用在线信息覆盖（如果有）
            # 添加一个标记，标识数据来源
            merged_data['_data_sources'] = {
                'config': gw_data,
                'online': online_info
            }
            
            # 查找或创建网关记录
            gateway = self.db.query(Gateway).filter(
                and_(
                    Gateway.vos_instance_id == self.vos_instance_id,
                    Gateway.gateway_name == gateway_name
                )
            ).first()
            
            # 将VOS API字段映射到Gateway模型字段
            gateway_fields = self._map_gateway_fields(gw_data, online_info, is_online, gw_type)
            
            if gateway:
                # 更新现有记录
                for key, value in gateway_fields.items():
                    if hasattr(gateway, key):
                        setattr(gateway, key, value)
                # 更新vos_uuid（如果VOS实例存在）
                if self.vos_instance and self.vos_instance.vos_uuid:
                    gateway.vos_uuid = self.vos_instance.vos_uuid
                # 保存完整数据
                gateway.raw_data = merged_data
                gateway.synced_at = datetime.utcnow()
            else:
                # 创建新记录
                gateway_fields['vos_instance_id'] = self.vos_instance_id
                gateway_fields['vos_uuid'] = self.vos_instance.vos_uuid if self.vos_instance and self.vos_instance.vos_uuid else None
                gateway_fields['raw_data'] = merged_data
                gateway = Gateway(**gateway_fields)
                self.db.add(gateway)
            
            synced_count += 1
        
        try:
            self.db.commit()
            logger.debug(f"{gw_type} 网关数据已提交到数据库 (instance={self.vos_instance_id}, count={synced_count})")
        except Exception as e:
            logger.error(f"提交网关数据到数据库失败 (type={gw_type}, instance={self.vos_instance_id}): {e}")
            self.db.rollback()
            raise
        
        # 4. 同时更新通用缓存
        self.cache_service._save_to_cache(
            vos_instance_id=self.vos_instance_id,
            api_path=api_path,
            cache_key=VosCacheService.generate_cache_key(api_path, {}),
            params={},
            response_data=config_result,
            is_valid=True,
            ret_code=0,
            error_message=None
        )
        
        logger.info(f"{gw_type} 网关同步完成: {synced_count} 个")
        return {'success': True, 'count': synced_count}
    
    # ==================== 费率组同步（新增）====================
    
    def sync_fee_rate_groups(self) -> Dict[str, Any]:
        """同步费率组"""
        logger.info(f"开始同步费率组 (instance={self.vos_instance_id})")
        
        try:
            # 调用 VOS API
            result = self.client.call_api('/external/server/GetFeeRateGroup', {})
            
            if not self.client.is_success(result):
                error_msg = self.client.get_error_message(result)
                logger.error(f"获取费率组失败: {error_msg}")
                return {'success': False, 'error': error_msg}
            
            # 解析费率组数据
            groups_data = result.get('infoFeeRateGroups', [])
            synced_count = 0
            
            for group_data in groups_data:
                group_name = group_data.get('name')
                if not group_name:
                    continue
                
                # 查找或创建费率组记录
                group = self.db.query(FeeRateGroup).filter(
                    and_(
                        FeeRateGroup.vos_instance_id == self.vos_instance_id,
                        FeeRateGroup.group_name == group_name
                    )
                ).first()
                
                if group:
                    # 更新现有记录
                    group.description = group_data.get('description')
                    group.raw_data = group_data
                    group.synced_at = datetime.utcnow()
                else:
                    # 创建新记录
                    group = FeeRateGroup(
                        vos_instance_id=self.vos_instance_id,
                        group_name=group_name,
                        description=group_data.get('description'),
                        raw_data=group_data
                    )
                    self.db.add(group)
                
                synced_count += 1
            
            self.db.commit()
            
            # 同时更新通用缓存
            self.cache_service._save_to_cache(
                vos_instance_id=self.vos_instance_id,
                api_path='/external/server/GetFeeRateGroup',
                cache_key=VosCacheService.generate_cache_key('/external/server/GetFeeRateGroup', {}),
                params={},
                response_data=result,
                is_valid=True,
                ret_code=0,
                error_message=None
            )
            
            logger.info(f"费率组同步完成: {synced_count} 个")
            return {'success': True, 'count': synced_count}
            
        except Exception as e:
            logger.exception(f"同步费率组失败: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    # ==================== 套餐同步（新增）====================
    
    def sync_suites(self) -> Dict[str, Any]:
        """同步套餐"""
        logger.info(f"开始同步套餐 (instance={self.vos_instance_id})")
        
        try:
            # 调用 VOS API
            result = self.client.call_api('/external/server/GetSuite', {})
            
            if not self.client.is_success(result):
                error_msg = self.client.get_error_message(result)
                logger.error(f"获取套餐失败: {error_msg}")
                return {'success': False, 'error': error_msg}
            
            # 解析套餐数据
            suites_data = result.get('infoSuites', [])
            synced_count = 0
            
            for suite_data in suites_data:
                suite_id = str(suite_data.get('id') or suite_data.get('suiteId', ''))
                if not suite_id:
                    continue
                
                # 查找或创建套餐记录
                suite = self.db.query(Suite).filter(
                    and_(
                        Suite.vos_instance_id == self.vos_instance_id,
                        Suite.suite_id == suite_id
                    )
                ).first()
                
                if suite:
                    # 更新现有记录
                    suite.suite_name = suite_data.get('name')
                    suite.suite_type = suite_data.get('type')
                    suite.price = float(suite_data.get('price', 0))
                    suite.monthly_fee = float(suite_data.get('monthlyFee', 0))
                    suite.duration = int(suite_data.get('duration', 0))
                    suite.raw_data = suite_data
                    suite.synced_at = datetime.utcnow()
                else:
                    # 创建新记录
                    suite = Suite(
                        vos_instance_id=self.vos_instance_id,
                        suite_id=suite_id,
                        suite_name=suite_data.get('name'),
                        suite_type=suite_data.get('type'),
                        price=float(suite_data.get('price', 0)),
                        monthly_fee=float(suite_data.get('monthlyFee', 0)),
                        duration=int(suite_data.get('duration', 0)),
                        raw_data=suite_data
                    )
                    self.db.add(suite)
                
                synced_count += 1
            
            self.db.commit()
            
            # 同时更新通用缓存
            self.cache_service._save_to_cache(
                vos_instance_id=self.vos_instance_id,
                api_path='/external/server/GetSuite',
                cache_key=VosCacheService.generate_cache_key('/external/server/GetSuite', {}),
                params={},
                response_data=result,
                is_valid=True,
                ret_code=0,
                error_message=None
            )
            
            logger.info(f"套餐同步完成: {synced_count} 个")
            return {'success': True, 'count': synced_count}
            
        except Exception as e:
            logger.exception(f"同步套餐失败: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}

