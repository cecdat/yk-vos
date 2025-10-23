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
        
        try:
            # 同步对接网关
            if gateway_type in ['mapping', 'both']:
                results['mapping'] = self._sync_gateway_type('mapping')
            
            # 同步落地网关
            if gateway_type in ['routing', 'both']:
                results['routing'] = self._sync_gateway_type('routing')
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.exception(f"同步网关失败: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def _sync_gateway_type(self, gw_type: str) -> Dict[str, Any]:
        """同步特定类型的网关"""
        api_path = f'/external/server/GetGateway{"Mapping" if gw_type == "mapping" else "Routing"}'
        api_path_online = f'{api_path}Online'
        
        # 1. 获取网关配置
        config_result = self.client.call_api(api_path, {'names': []})
        if not self.client.is_success(config_result):
            return {'success': False, 'error': self.client.get_error_message(config_result)}
        
        # 2. 获取在线状态
        online_result = self.client.call_api(api_path_online, {'names': []})
        online_data = {}
        if self.client.is_success(online_result):
            online_list = online_result.get('infoGatewayMappingsOnline' if gw_type == 'mapping' else 'infoGatewayRoutingsOnline', [])
            for gw in online_list:
                name = gw.get('name')
                if name:
                    online_data[name] = gw
        
        # 3. 更新到专门表
        gateways_list = config_result.get('infoGatewayMappings' if gw_type == 'mapping' else 'infoGatewayRoutings', [])
        synced_count = 0
        
        for gw_data in gateways_list:
            gateway_name = gw_data.get('name')
            if not gateway_name:
                continue
            
            # 获取在线状态和性能数据
            online_info = online_data.get(gateway_name, {})
            is_online = online_info.get('isOnline', False) or online_info.get('online', False)
            
            # 查找或创建网关记录
            gateway = self.db.query(Gateway).filter(
                and_(
                    Gateway.vos_instance_id == self.vos_instance_id,
                    Gateway.gateway_name == gateway_name
                )
            ).first()
            
            if gateway:
                # 更新现有记录
                gateway.gateway_type = gw_type
                gateway.is_online = is_online
                gateway.ip_address = gw_data.get('ipAddress') or gw_data.get('ip')
                gateway.port = gw_data.get('port')
                gateway.protocol = gw_data.get('protocol')
                gateway.asr = online_info.get('asr', 0.0)
                gateway.acd = online_info.get('acd', 0.0)
                gateway.concurrent_calls = online_info.get('concurrentCalls', 0)
                gateway.raw_data = {**gw_data, **online_info}
                gateway.synced_at = datetime.utcnow()
            else:
                # 创建新记录
                gateway = Gateway(
                    vos_instance_id=self.vos_instance_id,
                    gateway_name=gateway_name,
                    gateway_type=gw_type,
                    is_online=is_online,
                    ip_address=gw_data.get('ipAddress') or gw_data.get('ip'),
                    port=gw_data.get('port'),
                    protocol=gw_data.get('protocol'),
                    asr=online_info.get('asr', 0.0),
                    acd=online_info.get('acd', 0.0),
                    concurrent_calls=online_info.get('concurrentCalls', 0),
                    raw_data={**gw_data, **online_info}
                )
                self.db.add(gateway)
            
            synced_count += 1
        
        self.db.commit()
        
        # 4. 同时更新通用缓存
        self.cache_service._save_to_cache(
            vos_instance_id=self.vos_instance_id,
            api_path=api_path,
            cache_key=VosCacheService.generate_cache_key(api_path, {'names': []}),
            params={'names': []},
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
            result = self.client.call_api('/external/server/GetFeeRateGroup', {'names': []})
            
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
                cache_key=VosCacheService.generate_cache_key('/external/server/GetFeeRateGroup', {'names': []}),
                params={'names': []},
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
            result = self.client.call_api('/external/server/GetSuite', {'ids': []})
            
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
                cache_key=VosCacheService.generate_cache_key('/external/server/GetSuite', {'ids': []}),
                params={'ids': []},
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

