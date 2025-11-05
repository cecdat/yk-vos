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
            # 多天同步：按天创建多个任务
            from app.tasks.initial_sync_tasks import sync_cdrs_for_single_day
            from app.models.customer import Customer as CustomerModel
            
            # 创建一个专门的任务来同步单个客户的单天数据
            # 我们需要创建一个新的任务函数，或者修改现有的 sync_cdrs_for_single_day 来支持单个客户
            
            # 临时方案：为每天创建一个任务，但任务中只同步该客户
            # 我们需要修改 sync_cdrs_for_single_day 来支持可选的 customer_account 参数
            # 或者创建一个新的任务函数
            
            # 这里先使用简单方案：按天循环，每天创建一个任务同步该客户
            today = datetime.now().date()
            task_count = 0
            task_ids = []
            
            logger.info(f'📅 为客户 {customer.account} 创建 {days} 天的同步任务（避免一次性查询导致VOS卡死）')
            
            for day_offset in range(days):
                sync_date = today - timedelta(days=day_offset)
                date_str = sync_date.strftime('%Y%m%d')
                
                # 创建任务：同步该客户当天的话单
                # 注意：这里需要创建一个新的任务函数来支持单个客户同步
                # 暂时使用 sync_cdrs_for_single_day，但需要修改它以支持单个客户过滤
                # 或者创建一个新的任务函数 sync_single_customer_single_day
                
                # 临时方案：创建一个任务，传入 customer_account 参数
                # 我们需要先创建一个新的任务函数
                delay_seconds = day_offset * 10  # 每天间隔10秒
                
                # 调用单个客户单天同步任务
                task = sync_single_customer_single_day.apply_async(
                    args=[instance_id, customer_id, date_str],
                    countdown=delay_seconds
                )
                task_ids.append(str(task.id))
                task_count += 1
                
                logger.info(f'  📅 已创建任务: {customer.account} - {date_str} (将在{delay_seconds}秒后执行)')
            
            logger.info(f'✅ 已为客户 {customer.account} 创建 {task_count} 个同步任务')
            
            return {
                'success': True,
                'customer': customer.account,
                'instance': inst.name,
                'days': days,
                'total_tasks': task_count,
                'task_ids': task_ids,
                'message': f'已创建{task_count}个同步任务，任务将按计划执行'
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

