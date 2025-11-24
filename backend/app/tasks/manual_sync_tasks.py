"""
手动触发的同步任务
支持更精细的同步控制
"""
from app.tasks.celery_app import celery
from app.core.db import SessionLocal
from app.models.vos_instance import VOSInstance
from app.models.customer import Customer
from app.core.vos_client import VOSClient
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


@celery.task
def sync_single_customer_cdrs(instance_id: int, customer_id: int, days: int = 1):
    """
    同步单个客户的历史话单到ClickHouse（按天创建任务，避免VOS卡死）
    
    Args:
        instance_id: VOS实例ID
        customer_id: 客户ID
        days: 同步天数
    """
    db = SessionLocal()
    from app.models.clickhouse_cdr import ClickHouseCDR
    from app.core.vos_client import VOSClient
    import redis
    from app.core.config import settings
    
    # 连接 Redis 用于存储同步进度
    try:
        r = redis.from_url(settings.REDIS_URL)
    except Exception as e:
        logger.error(f'连接 Redis 失败: {e}')
        r = None
    
    try:
        # 获取实例和客户信息
        inst = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
        if not inst:
            logger.error(f'VOS实例 {instance_id} 未找到')
            return {'success': False, 'message': 'VOS实例未找到'}
        
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.vos_instance_id == instance_id
        ).first()
        if not customer:
            logger.error(f'客户 {customer_id} 未找到')
            return {'success': False, 'message': '客户未找到'}
        
        logger.info(f'📞 开始同步单个客户话单: {inst.name} - {customer.account} (最近{days}天)')
        
        # 如果只有1天，直接同步
        if days == 1:
            today = datetime.now().date()
            date_str = today.strftime('%Y%m%d')
            
            client = VOSClient(inst.base_url)
            
            # 更新同步进度
            if r:
                r.setex(
                    'cdr_sync_progress',
                    3600,
                    json.dumps({
                        'status': 'syncing',
                        'current_instance': inst.name,
                        'current_instance_id': inst.id,
                        'current_customer': customer.account,
                        'current_customer_index': 1,
                        'total_customers': 1,
                        'synced_count': 0,
                        'start_time': datetime.now().isoformat(),
                        'sync_date': date_str
                    }, ensure_ascii=False)
                )
            
            # 查询该客户当天的话单
            payload = {
                'accounts': [customer.account],
                'callerE164': None,
                'calleeE164': None,
                'callerGateway': None,
                'calleeGateway': None,
                'beginTime': date_str,
                'endTime': date_str
            }
            
            try:
                res = client.post('/external/server/GetCdr', payload=payload)
                
                if not isinstance(res, dict) or res.get('retCode') != 0:
                    error_msg = res.get('exception', 'Unknown error') if isinstance(res, dict) else 'Invalid response'
                    logger.warning(f'客户 {customer.account} 话单查询失败: {error_msg}')
                    if r:
                        r.delete('cdr_sync_progress')
                    return {
                        'success': False,
                        'message': f'VOS API错误: {error_msg}',
                        'customer': customer.account
                    }
                
                # 提取话单列表
                cdrs = res.get('infoCdrs') or res.get('cdrs') or res.get('CDRList') or []
                if not isinstance(cdrs, list):
                    for v in res.values():
                        if isinstance(v, list):
                            cdrs = v
                            break
                
                total_synced = 0
                if cdrs:
                    inserted = ClickHouseCDR.insert_cdrs(cdrs, vos_id=inst.id, vos_uuid=str(inst.vos_uuid))
                    total_synced += inserted
                    logger.info(f'✅ 客户 {customer.account}: 同步 {inserted} 条话单')
                else:
                    logger.info(f'客户 {customer.account} 没有话单数据')
                
                if r:
                    r.delete('cdr_sync_progress')
                
                return {
                    'success': True,
                    'synced_count': total_synced,
                    'customer': customer.account,
                    'instance': inst.name,
                    'days': 1
                }
                
            except Exception as e:
                logger.exception(f'客户 {customer.account} 同步失败: {e}')
                if r:
                    r.delete('cdr_sync_progress')
                return {
                    'success': False,
                    'message': f'同步失败: {str(e)}',
                    'customer': customer.account
                }
        else:
            # 多天同步：顺序执行（不再拆分任务）
            today = datetime.now().date()
            total_synced = 0
            
            logger.info(f'📅 开始顺序同步客户 {customer.account} 最近 {days} 天的话单...')
            
            client = VOSClient(inst.base_url)
            
            for day_offset in range(days):
                sync_date = today - timedelta(days=day_offset)
                date_str = sync_date.strftime('%Y%m%d')
                
                logger.info(f'  📅 处理日期: {date_str} (第 {day_offset+1}/{days} 天)')
                
                # 更新同步进度
                if r:
                    r.setex(
                        'cdr_sync_progress',
                        3600,
                        json.dumps({
                            'status': 'syncing',
                            'current_instance': inst.name,
                            'current_instance_id': inst.id,
                            'current_customer': customer.account,
                            'current_day': day_offset + 1,
                            'total_days': days,
                            'synced_count': total_synced,
                            'start_time': datetime.now().isoformat(),
                            'sync_date': date_str
                        }, ensure_ascii=False)
                    )
                
                # 计算开始时间和结束时间 (begin=date-1, end=date)
                try:
                    end_date = datetime.strptime(date_str, '%Y%m%d')
                    start_date = end_date - timedelta(days=1)
                    
                    begin_time = start_date.strftime('%Y%m%d')
                    end_time = date_str
                except Exception as e:
                    logger.error(f'日期格式解析失败: {date_str}, error: {e}')
                    begin_time = date_str
                    end_time = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
                
                # 查询该客户当天的话单
                payload = {
                    'accounts': [customer.account],
                    'callerE164': None,
                    'calleeE164': None,
                    'callerGateway': None,
                    'calleeGateway': None,
                    'beginTime': begin_time,
                    'endTime': end_time
                }
                
                try:
                    res = client.post('/external/server/GetCdr', payload=payload)
                    
                    if not isinstance(res, dict) or res.get('retCode') != 0:
                        error_msg = res.get('exception', 'Unknown error') if isinstance(res, dict) else 'Invalid response'
                        logger.warning(f'    ❌ 客户 {customer.account} ({date_str}) 话单查询失败: {error_msg}')
                        continue
                    
                    # 提取话单列表
                    cdrs = res.get('infoCdrs') or res.get('cdrs') or res.get('CDRList') or []
                    if not isinstance(cdrs, list):
                        for v in res.values():
                            if isinstance(v, list):
                                cdrs = v
                                break
                    
                    if cdrs:
                        inserted = ClickHouseCDR.insert_cdrs(cdrs, vos_id=inst.id, vos_uuid=str(inst.vos_uuid))
                        total_synced += inserted
                        logger.info(f'    ✅ 同步成功: {inserted} 条话单')
                    else:
                        logger.info(f'    ℹ️  无话单数据')
                        
                except Exception as e:
                    logger.exception(f'    ❌ 同步失败: {e}')
                    continue
            
            logger.info(f'✅ 客户 {customer.account} 同步完成，共 {total_synced} 条话单')
            
            if r:
                r.delete('cdr_sync_progress')
            
            return {
                'success': True,
                'customer': customer.account,
                'instance': inst.name,
                'days': days,
                'total_synced': total_synced,
                'message': f'同步完成，共 {total_synced} 条话单'
            }
    
    except Exception as e:
        logger.exception(f'同步客户 {customer_id} 话单时发生错误: {e}')
        if r:
            r.delete('cdr_sync_progress')
        return {'success': False, 'message': str(e)}
    finally:
        db.close()


@celery.task
def sync_single_customer_single_day(instance_id: int, customer_id: int, date_str: str):
    """
    同步单个客户的单天话单到ClickHouse
    
    Args:
        instance_id: VOS实例ID
        customer_id: 客户ID
        date_str: 日期字符串，格式：YYYYMMDD
    """
    db = SessionLocal()
    from app.models.clickhouse_cdr import ClickHouseCDR
    from app.core.vos_client import VOSClient
    import redis
    from app.core.config import settings
    
    # 连接 Redis 用于存储同步进度
    try:
        r = redis.from_url(settings.REDIS_URL)
    except Exception as e:
        logger.error(f'连接 Redis 失败: {e}')
        r = None
    
    try:
        # 获取实例和客户信息
        inst = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
        if not inst:
            logger.error(f'VOS实例 {instance_id} 未找到')
            return {'success': False, 'message': 'VOS实例未找到'}
        
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.vos_instance_id == instance_id
        ).first()
        if not customer:
            logger.error(f'客户 {customer_id} 未找到')
            return {'success': False, 'message': '客户未找到'}
        
        logger.info(f'📞 同步客户话单: {inst.name} - {customer.account} - {date_str}')
        
        client = VOSClient(inst.base_url)
        
        # 更新同步进度
        if r:
            r.setex(
                'cdr_sync_progress',
                3600,
                json.dumps({
                    'status': 'syncing',
                    'current_instance': inst.name,
                    'current_instance_id': inst.id,
                    'current_customer': customer.account,
                    'current_customer_index': 1,
                    'total_customers': 1,
                    'synced_count': 0,
                    'start_time': datetime.now().isoformat(),
                    'sync_date': date_str
                }, ensure_ascii=False)
            )
        
        # 计算开始时间和结束时间 (begin=date-1, end=date)
        try:
            end_date = datetime.strptime(date_str, '%Y%m%d')
            start_date = end_date - timedelta(days=1)
            
            begin_time = start_date.strftime('%Y%m%d')
            end_time = date_str
        except Exception as e:
            logger.error(f'日期格式解析失败: {date_str}, error: {e}')
            begin_time = date_str
            end_time = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
        
        # 查询该客户当天的话单
        payload = {
            'accounts': [customer.account],
            'callerE164': None,
            'calleeE164': None,
            'callerGateway': None,
            'calleeGateway': None,
            'beginTime': begin_time,
            'endTime': end_time
        }
        
        try:
            res = client.post('/external/server/GetCdr', payload=payload)
            
            if not isinstance(res, dict) or res.get('retCode') != 0:
                error_msg = res.get('exception', 'Unknown error') if isinstance(res, dict) else 'Invalid response'
                logger.warning(f'客户 {customer.account} 话单查询失败: {error_msg}')
                if r:
                    r.delete('cdr_sync_progress')
                return {
                    'success': False,
                    'message': f'VOS API错误: {error_msg}',
                    'customer': customer.account,
                    'date': date_str
                }
            
            # 提取话单列表
            cdrs = res.get('infoCdrs') or res.get('cdrs') or res.get('CDRList') or []
            if not isinstance(cdrs, list):
                for v in res.values():
                    if isinstance(v, list):
                        cdrs = v
                        break
            
            total_synced = 0
            if cdrs:
                inserted = ClickHouseCDR.insert_cdrs(cdrs, vos_id=inst.id, vos_uuid=str(inst.vos_uuid))
                total_synced += inserted
                logger.info(f'✅ 客户 {customer.account} ({date_str}): 同步 {inserted} 条话单')
            else:
                logger.info(f'客户 {customer.account} ({date_str}) 没有话单数据')
            
            if r:
                r.delete('cdr_sync_progress')
            
            return {
                'success': True,
                'synced_count': total_synced,
                'customer': customer.account,
                'instance': inst.name,
                'date': date_str
            }
            
        except Exception as e:
            logger.exception(f'客户 {customer.account} ({date_str}) 同步失败: {e}')
            if r:
                r.delete('cdr_sync_progress')
            return {
                'success': False,
                'message': f'同步失败: {str(e)}',
                'customer': customer.account,
                'date': date_str
            }
    
    except Exception as e:
        logger.exception(f'同步客户 {customer_id} 话单时发生错误: {e}')
        if r:
            r.delete('cdr_sync_progress')
        return {'success': False, 'message': str(e)}
    finally:
        db.close()

