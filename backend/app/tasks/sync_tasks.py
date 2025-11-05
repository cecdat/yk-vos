from app.tasks.celery_app import celery
from app.core.db import SessionLocal
from app.models.vos_instance import VOSInstance
from app.models.phone import Phone
from app.models.cdr import CDR
from app.models.customer import Customer
from app.models.vos_data_cache import VosDataCache
from app.models.vos_health import VOSHealthCheck
from app.core.vos_client import VOSClient
from app.core.vos_cache_service import VosCacheService
from app.core.vos_sync_enhanced import VosSyncEnhanced
from datetime import datetime, timedelta
import logging, json, hashlib, time
from dateutil import parser as dateparser
logger = logging.getLogger(__name__)

def get_vos_uuid_by_instance_id(db, instance_id):
    """根据VOS实例ID获取对应的UUID"""
    instance = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
    return instance.vos_uuid if instance else None

@celery.task
def sync_all_instances_online_phones():
    db = SessionLocal()
    try:
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        if not instances:
            logger.info('没有启用的VOS实例，跳过同步在线话机任务')
            return {'success': True, 'message': '没有VOS实例需要同步', 'instances_count': 0}
        
        for inst in instances:
            client = VOSClient(inst.base_url)
            res = client.post('/external/server/GetAllPhoneOnline', payload={})
            phones = res.get('infoPhoneOnlines') or res.get('phones') or []
            if not isinstance(phones, list):
                for v in res.values():
                    if isinstance(v, list):
                        phones = v
                        break
            for p in phones:
                e164 = p.get('e164') or p.get('E164') or p.get('account') or ''
                if not e164:
                    continue
                existing = db.query(Phone).filter(Phone.e164 == e164, Phone.vos_id == inst.id).first()
                if existing:
                    existing.status = 'online'
                    existing.vos_uuid = inst.vos_uuid  # 更新UUID
                else:
                    newp = Phone(e164=e164, status='online', vos_id=inst.id, vos_uuid=inst.vos_uuid)
                    db.add(newp)
            db.commit()
    except Exception as e:
        logger.exception('Error syncing phones: %s', e)
    finally:
        db.close()

@celery.task
def sync_all_instances_cdrs(days=1):
    """
    定时同步所有VOS实例的历史话单到ClickHouse（优化版）
    
    同步策略：
    1. 检查是否有VOS节点，没有则跳过
    2. 先同步客户信息
    3. 按客户维度同步历史话单
    4. 实时更新同步进度到Redis
    """
    db = SessionLocal()
    from app.models.clickhouse_cdr import ClickHouseCDR
    from app.core.config import settings
    import redis
    
    # 连接 Redis 用于存储同步进度
    try:
        r = redis.from_url(settings.REDIS_URL)
    except Exception as e:
        logger.error(f'连接 Redis 失败: {e}')
        r = None
    
    try:
        # 1. 检查是否有启用的VOS实例
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        if not instances:
            logger.info('没有启用的VOS实例，跳过同步话单任务')
            return {'success': True, 'message': '没有VOS实例需要同步', 'instances_count': 0}
        
        results = []
        total_synced = 0
        
        for inst in instances:
            logger.info(f'🚀 开始同步 VOS 实例: {inst.name}')
            
            # 更新同步进度：当前实例
            if r:
                r.setex(
                    'cdr_sync_progress',
                    3600,  # 1小时过期
                    json.dumps({
                        'status': 'syncing',
                        'current_instance': inst.name,
                        'current_instance_id': inst.id,
                        'current_customer': None,
                        'synced_count': total_synced,
                        'start_time': datetime.now().isoformat()
                    }, ensure_ascii=False)
                )
            
            # 2. 先同步客户信息
            logger.info(f'📋 步骤1: 同步客户信息...')
            customer_result = sync_customers_for_instance(inst.id)
            if not customer_result.get('success'):
                logger.error(f'客户信息同步失败: {customer_result.get("message")}')
                results.append({
                    'instance_id': inst.id,
                    'instance_name': inst.name,
                    'success': False,
                    'error': f'客户同步失败: {customer_result.get("message")}'
                })
                continue
            
            # 3. 获取客户列表
            customers = db.query(Customer).filter(
                Customer.vos_instance_id == inst.id
            ).all()
            
            if not customers:
                logger.warning(f'VOS {inst.name} 没有客户数据，跳过话单同步')
                results.append({
                    'instance_id': inst.id,
                    'instance_name': inst.name,
                    'success': True,
                    'synced_count': 0,
                    'message': '没有客户数据'
                })
                continue
            
            logger.info(f'📞 步骤2: 按客户同步历史话单 (共 {len(customers)} 个客户)...')
            
            # 4. 按客户循环同步话单
            instance_synced = 0
            client = VOSClient(inst.base_url)
            end = datetime.utcnow()
            start = end - timedelta(days=days)
            
            for idx, customer in enumerate(customers, 1):
                account = customer.account
                logger.info(f'  [{idx}/{len(customers)}] 同步客户: {account}')
                
                # 更新同步进度：当前客户
                if r:
                    r.setex(
                        'cdr_sync_progress',
                        3600,
                        json.dumps({
                            'status': 'syncing',
                            'current_instance': inst.name,
                            'current_instance_id': inst.id,
                            'current_customer': account,
                            'current_customer_index': idx,
                            'total_customers': len(customers),
                            'synced_count': total_synced + instance_synced,
                            'start_time': datetime.now().isoformat()
                        }, ensure_ascii=False)
                    )
                
                # 查询该客户的话单
                payload = {
                    'accounts': [account],
                    'callerE164': None,
                    'calleeE164': None,
                    'callerGateway': None,
                    'calleeGateway': None,
                    'beginTime': start.strftime('%Y%m%d'),
                    'endTime': end.strftime('%Y%m%d')
                }
                
                try:
                    res = client.post('/external/server/GetCdr', payload=payload)
                    
                    if not isinstance(res, dict) or res.get('retCode') != 0:
                        logger.warning(f'    客户 {account} 话单查询失败')
                        continue
                    
                    cdrs = res.get('infoCdrs') or res.get('cdrs') or res.get('CDRList') or []
                    if not isinstance(cdrs, list):
                        for v in res.values():
                            if isinstance(v, list):
                                cdrs = v
                                break
                    
                    if cdrs:
                        inserted = ClickHouseCDR.insert_cdrs(cdrs, vos_id=inst.id, vos_uuid=str(inst.vos_uuid))
                        instance_synced += inserted
                        logger.info(f'    ✅ 客户 {account}: 同步 {inserted} 条话单')
                    
                except Exception as e:
                    logger.exception(f'    ❌ 客户 {account} 同步失败: {e}')
                    continue
            
            total_synced += instance_synced
            logger.info(f'✅ VOS {inst.name} 话单同步完成: 共 {instance_synced} 条')
            
            results.append({
                'instance_id': inst.id,
                'instance_name': inst.name,
                'success': True,
                'synced_count': instance_synced,
                'customers_count': len(customers)
            })
        
        # 清除同步进度（完成）
        if r:
            r.delete('cdr_sync_progress')
        
        return {
            'success': True,
            'instances_count': len(instances),
            'total_synced': total_synced,
            'results': results
        }
        
    except Exception as e:
        logger.exception(f'Error syncing CDRs: {e}')
        # 清除同步进度（错误）
        if r:
            r.delete('cdr_sync_progress')
        return {'success': False, 'message': str(e)}
    finally:
        db.close()


@celery.task
def sync_customers_for_instance(instance_id: int):
    """同步单个VOS实例的客户数据"""
    db = SessionLocal()
    try:
        inst = db.query(VOSInstance).filter(VOSInstance.id == instance_id, VOSInstance.enabled == True).first()
        if not inst:
            logger.warning(f'VOS实例 {instance_id} 未找到或已禁用')
            return {'success': False, 'message': 'VOS实例未找到或已禁用'}
        
        client = VOSClient(inst.base_url)
        
        # 调用VOS API获取客户列表
        try:
            result = client.call_api('/external/server/GetAllCustomers', {'type': 1})
        except Exception as e:
            logger.exception(f'从VOS {inst.name} 获取客户数据失败: {e}')
            return {'success': False, 'message': str(e)}
        
        if not client.is_success(result):
            error_msg = client.get_error_message(result)
            logger.error(f'VOS {inst.name} API错误: {error_msg}')
            return {'success': False, 'message': error_msg}
        
        # 解析客户数据
        customers = result.get('infoCustomerBriefs', [])
        if not isinstance(customers, list):
            logger.warning(f'VOS {inst.name} 返回的客户数据格式异常')
            return {'success': False, 'message': '客户数据格式无效'}
        
        # 同步到数据库
        synced_count = 0
        updated_count = 0
        
        for cust_data in customers:
            account = cust_data.get('account')
            if not account:
                continue
            
            money = float(cust_data.get('money', 0.0))
            limit_money = float(cust_data.get('limitMoney', 0.0))
            is_in_debt = money < 0
            
            # 将完整的VOS客户数据保存为JSON字符串
            raw_data_json = json.dumps(cust_data, ensure_ascii=False)
            
            # 查找现有记录
            existing = db.query(Customer).filter(
                Customer.vos_instance_id == instance_id,
                Customer.account == account
            ).first()
            
            if existing:
                # 更新现有记录（包括完整的原始数据）
                existing.money = money
                existing.limit_money = limit_money
                existing.is_in_debt = is_in_debt
                existing.raw_data = raw_data_json
                existing.vos_uuid = inst.vos_uuid  # 更新UUID
                existing.synced_at = datetime.utcnow()
                updated_count += 1
            else:
                # 创建新记录（包括完整的原始数据）
                new_customer = Customer(
                    vos_instance_id=instance_id,
                    vos_uuid=inst.vos_uuid,
                    account=account,
                    money=money,
                    limit_money=limit_money,
                    is_in_debt=is_in_debt,
                    raw_data=raw_data_json
                )
                db.add(new_customer)
                synced_count += 1
        
        db.commit()
        
        total = synced_count + updated_count
        logger.info(f'VOS {inst.name} 客户同步完成: 共 {total} 个客户 (新增: {synced_count}, 更新: {updated_count})')
        
        # 在客户数据同步完成后，刷新仪表盘统计视图
        try:
            from app.tasks.refresh_dashboard_statistics import refresh_dashboard_statistics_view
            refresh_dashboard_statistics_view.delay()
        except Exception as e:
            logger.warning(f'触发仪表盘统计视图刷新失败: {e}')

        return {
            'success': True,
            'total': total,
            'new': synced_count,
            'updated': updated_count,
            'instance_name': inst.name
        }
        
    except Exception as e:
        logger.exception(f'同步VOS实例 {instance_id} 客户数据时发生错误: {e}')
        db.rollback()
        return {'success': False, 'message': str(e)}
    finally:
        db.close()


@celery.task
def sync_all_instances_customers():
    """同步所有启用的VOS实例的客户数据（定时任务）"""
    db = SessionLocal()
    try:
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        if not instances:
            logger.info('没有启用的VOS实例，跳过同步客户数据任务')
            return {'success': True, 'message': '没有VOS实例需要同步', 'instances_count': 0}
        
        results = []
        
        for inst in instances:
            logger.info(f'开始同步VOS实例客户数据: {inst.name}')
            result = sync_customers_for_instance(inst.id)
            results.append({
                'instance_id': inst.id,
                'instance_name': inst.name,
                **result
            })
        
        return {
            'success': True,
            'instances_count': len(instances),
            'results': results
        }
        
    except Exception as e:
        logger.exception(f'同步所有VOS实例客户数据时发生错误: {e}')
        return {'success': False, 'message': str(e)}
    finally:
        db.close()


# ==================== 通用 VOS 数据同步任务 ====================

@celery.task
def sync_vos_api_data(instance_id: int, api_path: str, params: dict):
    """
    通用的 VOS API 数据同步任务
    
    Args:
        instance_id: VOS实例ID
        api_path: API路径
        params: 查询参数
    """
    db = SessionLocal()
    try:
        # 使用缓存服务，强制刷新数据
        cache_service = VosCacheService(db)
        data, source = cache_service.get_cached_data(
            vos_instance_id=instance_id,
            api_path=api_path,
            params=params,
            force_refresh=True
        )
        
        if source == 'vos_api' and data:
            logger.info(f'同步成功: {api_path} (instance={instance_id})')
            return {'success': True, 'api_path': api_path, 'instance_id': instance_id}
        else:
            logger.warning(f'同步失败: {api_path} (instance={instance_id}, source={source})')
            return {'success': False, 'api_path': api_path, 'instance_id': instance_id, 'source': source}
            
    except Exception as e:
        logger.exception(f'同步VOS数据失败: {api_path} (instance={instance_id}, error={e})')
        return {'success': False, 'api_path': api_path, 'instance_id': instance_id, 'error': str(e)}
    finally:
        db.close()


@celery.task
def sync_all_vos_common_apis():
    """
    同步所有VOS实例的常用API数据（定时任务）
    包括：客户列表、在线话机、网关状态、性能指标等
    """
    db = SessionLocal()
    try:
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        if not instances:
            logger.info('没有启用的VOS实例，跳过同步常用API任务')
            return {'success': True, 'message': '没有VOS实例需要同步', 'instances_count': 0}
        
        # 定义需要定期同步的API
        apis_to_sync = [
            # 实时数据（每30秒同步一次）
            {
                'api_path': '/external/server/GetAllPhoneOnline',
                'params': {},
                'interval': 30
            },
            {
                'api_path': '/external/server/GetGatewayMappingOnline',
                'params': {},
                'interval': 30
            },
            {
                'api_path': '/external/server/GetGatewayRoutingOnline',
                'params': {},
                'interval': 30
            },
            {
                'api_path': '/external/server/GetPerformance',
                'params': {},
                'interval': 30
            },
            # 准实时数据（每5分钟同步一次）
            {
                'api_path': '/external/server/GetAllCustomers',
                'params': {'type': 1},
                'interval': 300
            },
            # 配置数据（每小时同步一次）
            {
                'api_path': '/external/server/GetGatewayMapping',
                'params': {},
                'interval': 3600
            },
            {
                'api_path': '/external/server/GetGatewayRouting',
                'params': {},
                'interval': 3600
            },
            {
                'api_path': '/external/server/GetFeeRateGroup',
                'params': {},
                'interval': 3600
            },
            {
                'api_path': '/external/server/GetSoftSwitch',
                'params': {},
                'interval': 3600
            },
        ]
        
        results = []
        for inst in instances:
            logger.info(f'开始同步VOS实例常用API数据: {inst.name}')
            
            for api_config in apis_to_sync:
                api_path = api_config['api_path']
                params = api_config['params']
                
                # 检查缓存是否需要更新
                cache_service = VosCacheService(db)
                cache_key = VosCacheService.generate_cache_key(api_path, params)
                
                cached = db.query(VosDataCache).filter(
                    VosDataCache.vos_instance_id == inst.id,
                    VosDataCache.api_path == api_path,
                    VosDataCache.cache_key == cache_key,
                    VosDataCache.is_valid == True
                ).first()
                
                # 如果缓存不存在或已过期，则同步
                should_sync = False
                if not cached:
                    should_sync = True
                    logger.info(f'缓存不存在，需要同步: {api_path}')
                elif cached.is_expired():
                    should_sync = True
                    logger.info(f'缓存已过期，需要同步: {api_path}')
                
                if should_sync:
                    try:
                        data, source = cache_service.get_cached_data(
                            vos_instance_id=inst.id,
                            api_path=api_path,
                            params=params,
                            force_refresh=True
                        )
                        results.append({
                            'instance_id': inst.id,
                            'instance_name': inst.name,
                            'api_path': api_path,
                            'success': source == 'vos_api',
                            'source': source
                        })
                    except Exception as e:
                        logger.exception(f'同步失败: {api_path} (instance={inst.name}, error={e})')
                        results.append({
                            'instance_id': inst.id,
                            'instance_name': inst.name,
                            'api_path': api_path,
                            'success': False,
                            'error': str(e)
                        })
        
        success_count = sum(1 for r in results if r.get('success'))
        return {
            'success': True,
            'instances_count': len(instances),
            'total_synced': len(results),
            'success_count': success_count,
            'failed_count': len(results) - success_count,
            'details': results
        }
        
    except Exception as e:
        logger.exception(f'同步所有VOS实例常用API数据时发生错误: {e}')
        return {'success': False, 'message': str(e)}
    finally:
        db.close()


@celery.task
def cleanup_expired_cache():
    """清理过期的缓存数据（定时任务）"""
    db = SessionLocal()
    try:
        cache_service = VosCacheService(db)
        count = cache_service.cleanup_expired_cache(days=7)
        
        logger.info(f'清理过期缓存完成: 删除了 {count} 条记录')
        return {
            'success': True,
            'deleted_count': count,
            'message': f'清理了 {count} 条过期缓存记录'
        }
        
    except Exception as e:
        logger.exception(f'清理过期缓存失败: {e}')
        return {'success': False, 'message': str(e)}
    finally:
        db.close()


# ==================== 增强版同步任务（双写策略）====================

@celery.task
def sync_all_instances_enhanced():
    """
    增强版全量同步任务
    同步所有 VOS 实例的核心数据到专门表
    """
    db = SessionLocal()
    try:
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        if not instances:
            logger.info('没有启用的VOS实例，跳过增强版同步任务')
            return {'success': True, 'message': '没有VOS实例需要同步', 'instances_count': 0}
        
        results = []
        
        for inst in instances:
            logger.info(f'开始增强版同步: {inst.name}')
            
            sync_service = VosSyncEnhanced(db, inst.id, inst.base_url)
            
            # 1. 同步在线话机
            phones_result = sync_service.sync_phones_online()
            
            # 2. 同步网关（对接+落地）
            gateways_result = sync_service.sync_gateways('both')
            
            # 3. 同步费率组
            fee_rates_result = sync_service.sync_fee_rate_groups()
            
            # 4. 同步套餐
            suites_result = sync_service.sync_suites()
            
            results.append({
                'instance_id': inst.id,
                'instance_name': inst.name,
                'phones': phones_result,
                'gateways': gateways_result,
                'fee_rates': fee_rates_result,
                'suites': suites_result
            })
            
            logger.info(f'增强版同步完成: {inst.name}')
        
        return {
            'success': True,
            'instances_count': len(instances),
            'results': results
        }
        
    except Exception as e:
        logger.exception(f'增强版同步失败: {e}')
        return {'success': False, 'message': str(e)}
    finally:
        db.close()


@celery.task
def sync_instance_phones_enhanced(instance_id: int):
    """同步单个实例的在线话机（增强版）"""
    db = SessionLocal()
    try:
        inst = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
        if not inst:
            return {'success': False, 'message': 'VOS实例不存在'}
        
        sync_service = VosSyncEnhanced(db, inst.id, inst.base_url)
        result = sync_service.sync_phones_online()
        
        return {
            'success': result['success'],
            'instance_name': inst.name,
            **result
        }
        
    except Exception as e:
        logger.exception(f'同步话机失败: {e}')
        return {'success': False, 'message': str(e)}
    finally:
        db.close()


@celery.task
def sync_instance_gateways_enhanced(instance_id: int):
    """同步单个实例的网关（增强版）"""
    db = SessionLocal()
    try:
        inst = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
        if not inst:
            return {'success': False, 'message': 'VOS实例不存在'}
        
        sync_service = VosSyncEnhanced(db, inst.id, inst.base_url)
        result = sync_service.sync_gateways('both')
        
        return {
            'success': result['success'],
            'instance_name': inst.name,
            **result
        }
        
    except Exception as e:
        logger.exception(f'同步网关失败: {e}')
        return {'success': False, 'message': str(e)}
    finally:
        db.close()


@celery.task
def sync_all_instances_gateways():
    """
    同步所有VOS实例的网关数据（定时任务）
    每分钟运行一次，保持网关状态实时更新
    """
    db = SessionLocal()
    try:
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        if not instances:
            logger.info('没有启用的VOS实例，跳过网关同步任务')
            return {'success': True, 'message': '没有VOS实例需要同步', 'instances_count': 0}
        
        results = []
        for inst in instances:
            logger.info(f'开始同步网关: {inst.name}')
            
            try:
                sync_service = VosSyncEnhanced(db, inst.id, inst.base_url)
                
                # 同步网关（对接+落地）
                gateways_result = sync_service.sync_gateways('both')
                
                results.append({
                    'instance_id': inst.id,
                    'instance_name': inst.name,
                    'success': gateways_result.get('success', False),
                    'result': gateways_result
                })
            except Exception as e:
                logger.exception(f'同步网关失败 (instance={inst.name}): {e}')
                results.append({
                    'instance_id': inst.id,
                    'instance_name': inst.name,
                    'success': False,
                    'error': str(e)
                })
        
        success_count = sum(1 for r in results if r.get('success'))
        return {
            'success': True,
            'instances_count': len(instances),
            'success_count': success_count,
            'failed_count': len(instances) - success_count,
            'results': results
        }
        
    except Exception as e:
        logger.exception(f'同步所有实例网关失败: {e}')
        return {'success': False, 'message': str(e)}
    finally:
        db.close()


@celery.task
def check_vos_instances_health():
    """
    定时检查所有VOS实例的健康状态
    通过调用GetAllCustomers API来验证VOS接口是否畅通
    """
    db = SessionLocal()
    try:
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        if not instances:
            logger.info('没有启用的VOS实例，跳过健康检查')
            return {'success': True, 'message': '没有VOS实例需要检查', 'instances_count': 0}
        
        results = []
        for inst in instances:
            logger.info(f'检查VOS实例健康状态: {inst.name} ({inst.base_url})')
            
            # 获取或创建健康检查记录
            health_check = db.query(VOSHealthCheck).filter(
                VOSHealthCheck.vos_instance_id == inst.id
            ).first()
            
            if not health_check:
                health_check = VOSHealthCheck(vos_instance_id=inst.id, vos_uuid=inst.vos_uuid)
                db.add(health_check)
            else:
                # 更新现有记录的UUID
                health_check.vos_uuid = inst.vos_uuid
            
            # 执行健康检查 - 调用简单的API测试连通性
            client = VOSClient(inst.base_url)
            start_time = time.time()
            
            try:
                # 使用GetAllCustomers API作为健康检查
                result = client.post('/external/server/GetAllCustomers', payload={'type': 1})
                response_time = (time.time() - start_time) * 1000  # 转换为毫秒
                
                if client.is_success(result):
                    # API调用成功
                    health_check.status = 'healthy'
                    health_check.api_success = True
                    health_check.response_time_ms = response_time
                    health_check.error_message = None
                    health_check.consecutive_failures = 0
                    logger.info(f'✓ VOS实例 {inst.name} 健康 (响应时间: {response_time:.0f}ms)')
                else:
                    # API调用失败
                    error_msg = client.get_error_message(result)
                    health_check.status = 'unhealthy'
                    health_check.api_success = False
                    health_check.response_time_ms = response_time
                    health_check.error_message = error_msg[:500] if error_msg else 'API返回错误'
                    # 安全地增加失败次数
                    health_check.consecutive_failures = (health_check.consecutive_failures or 0) + 1
                    logger.warning(f'✗ VOS实例 {inst.name} 不健康: {error_msg}')
                
            except Exception as e:
                # 网络或其他错误
                response_time = (time.time() - start_time) * 1000
                error_msg = str(e)
                health_check.status = 'unhealthy'
                health_check.api_success = False
                health_check.response_time_ms = response_time
                health_check.error_message = error_msg[:500]
                # 安全地增加失败次数
                health_check.consecutive_failures = (health_check.consecutive_failures or 0) + 1
                logger.error(f'✗ VOS实例 {inst.name} 健康检查异常: {error_msg}')
            
            health_check.last_check_at = datetime.utcnow()
            
            results.append({
                'instance_id': inst.id,
                'instance_name': inst.name,
                'status': health_check.status,
                'response_time_ms': health_check.response_time_ms,
                'consecutive_failures': health_check.consecutive_failures
            })
        
        db.commit()
        logger.info(f'VOS健康检查完成，共检查 {len(instances)} 个实例')
        
        return {
            'success': True,
            'message': f'健康检查完成',
            'instances_count': len(instances),
            'results': results
        }
        
    except Exception as e:
        logger.exception(f'VOS健康检查任务失败: {e}')
        return {'success': False, 'message': str(e)}
    finally:
        db.close()
