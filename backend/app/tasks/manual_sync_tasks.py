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
    同步单个客户的历史话单到ClickHouse
    
    Args:
        instance_id: VOS实例ID
        customer_id: 客户ID
        days: 同步天数
    """
    db = SessionLocal()
    from app.models.clickhouse_cdr import ClickHouseCDR
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
        
        client = VOSClient(inst.base_url)
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        
        total_synced = 0
        
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
                    'start_time': datetime.now().isoformat()
                }, ensure_ascii=False)
            )
        
        # 查询该客户的话单
        payload = {
            'accounts': [customer.account],
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
                error_msg = res.get('exception', 'Unknown error') if isinstance(res, dict) else 'Invalid response'
                logger.warning(f'客户 {customer.account} 话单查询失败: {error_msg}')
                # 清除同步进度
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
            
            if cdrs:
                inserted = ClickHouseCDR.insert_cdrs(cdrs, vos_id=inst.id)
                total_synced += inserted
                logger.info(f'✅ 客户 {customer.account}: 同步 {inserted} 条话单')
                
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
                            'synced_count': inserted,
                            'start_time': datetime.now().isoformat()
                        }, ensure_ascii=False)
                    )
            else:
                logger.info(f'客户 {customer.account} 没有话单数据')
            
        except Exception as e:
            logger.exception(f'客户 {customer.account} 同步失败: {e}')
            # 清除同步进度
            if r:
                r.delete('cdr_sync_progress')
            return {
                'success': False,
                'message': f'同步失败: {str(e)}',
                'customer': customer.account
            }
        
        # 清除同步进度（完成）
        if r:
            r.delete('cdr_sync_progress')
        
        logger.info(f'✅ 客户 {customer.account} 话单同步完成: 共 {total_synced} 条')
        
        return {
            'success': True,
            'synced_count': total_synced,
            'customer': customer.account,
            'instance': inst.name,
            'days': days
        }
    
    except Exception as e:
        logger.exception(f'同步客户 {customer_id} 话单时发生错误: {e}')
        # 清除同步进度（错误）
        if r:
            r.delete('cdr_sync_progress')
        return {'success': False, 'message': str(e)}
    finally:
        db.close()

