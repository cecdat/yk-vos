"""
新增VOS节点后的初始化同步任务
分批同步历史数据，避免单次请求数据量过大导致超时
"""
from app.tasks.celery_app import celery
from app.core.db import SessionLocal
from app.models.vos_instance import VOSInstance
from app.models.customer import Customer
from app.models.cdr import CDR
from app.core.vos_client import VOSClient
from datetime import datetime, timedelta
import logging
import hashlib
import json
import time
from dateutil import parser as dateparser

logger = logging.getLogger(__name__)


@celery.task
def initial_sync_for_new_instance(instance_id: int, sync_days: int = 7):
    """
    新增VOS节点后的初始化同步任务（优化版 - 避免数据量过大）
    
    1. 首先同步客户数据
    2. 分批同步最近N天的历史话单（每天一批，间隔30秒）
    
    Args:
        instance_id: VOS实例ID
        sync_days: 同步最近多少天（默认7天，最大不超过30天）
    
    优化说明：
    - 对于上亿级话单，限制首次同步范围避免超时
    - 分批异步执行，避免并发过高
    - 可在业务低峰期延长同步天数
    """
    # ⚠️ 限制最大同步天数为30天（上亿级数据优化）
    if sync_days > 30:
        sync_days = 30
        logger.warning(f'⚠️ 同步天数限制为30天，避免数据量过大导致超时')
    db = SessionLocal()
    try:
        inst = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
        if not inst:
            logger.error(f'VOS实例 {instance_id} 未找到')
            return {'success': False, 'message': 'VOS实例未找到'}
        
        logger.info(f'🚀 开始初始化同步 VOS 实例: {inst.name} (ID={instance_id})')
        
        # 步骤1: 同步客户数据
        logger.info(f'📋 步骤1: 同步客户数据...')
        customer_result = sync_customers_for_new_instance(instance_id)
        
        if not customer_result.get('success'):
            logger.error(f'客户数据同步失败: {customer_result.get("message")}')
            return customer_result
        
        logger.info(f'✅ 客户数据同步完成: {customer_result.get("total", 0)} 个客户')
        
        # 步骤2: 异步分批同步最近N天的历史话单
        logger.info(f'📞 步骤2: 开始分批同步最近{sync_days}天的历史话单...')
        logger.info(f'💡 提示: 如数据量过大，可在业务低峰期手动触发更多天数的同步')
        
        # 创建N个异步任务，每个任务同步一天的数据
        today = datetime.now().date()
        for i in range(sync_days):
            sync_date = today - timedelta(days=i)
            # 延迟执行，避免并发过高
            delay_seconds = i * 30  # 每批间隔30秒
            
            sync_cdrs_for_single_day.apply_async(
                args=[instance_id, sync_date.strftime('%Y%m%d')],
                countdown=delay_seconds
            )
            
            logger.info(f'  📅 已创建任务: 同步 {sync_date} 的话单数据 (将在{delay_seconds}秒后执行)')
        
        return {
            'success': True,
            'message': f'初始化同步已启动（同步最近{sync_days}天数据）',
            'customers_synced': customer_result.get('total', 0),
            'cdr_sync_days': sync_days,
            'cdr_sync_tasks_created': sync_days,
            'instance_name': inst.name,
            'note': '如需同步更多历史数据，请在业务低峰期手动触发'
        }
        
    except Exception as e:
        logger.exception(f'初始化同步 VOS 实例 {instance_id} 时发生错误: {e}')
        return {'success': False, 'message': str(e)}
    finally:
        db.close()


def sync_customers_for_new_instance(instance_id: int):
    """
    同步新VOS实例的客户数据
    与 sync_customers_for_instance 功能相同，但明确用于新实例的初始化
    """
    db = SessionLocal()
    try:
        inst = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
        if not inst:
            return {'success': False, 'message': 'VOS实例未找到'}
        
        client = VOSClient(inst.base_url)
        
        try:
            result = client.call_api('/external/server/GetAllCustomers', {'type': 1})
        except Exception as e:
            logger.exception(f'从VOS {inst.name} 获取客户数据失败: {e}')
            return {'success': False, 'message': str(e)}
        
        if not client.is_success(result):
            error_msg = client.get_error_message(result)
            logger.error(f'VOS {inst.name} API错误: {error_msg}')
            return {'success': False, 'message': error_msg}
        
        customers = result.get('infoCustomerBriefs', [])
        if not customers:
            logger.warning(f'VOS {inst.name} 返回的客户列表为空')
            return {'success': True, 'total': 0, 'new': 0, 'updated': 0}
        
        total = len(customers)
        synced_count = 0
        updated_count = 0
        
        for customer_data in customers:
            account = customer_data.get('account') or customer_data.get('Account')
            if not account:
                continue
            
            money = customer_data.get('money', 0.0) or customer_data.get('Money', 0.0)
            limit_money = customer_data.get('limitMoney', 0.0) or customer_data.get('LimitMoney', 0.0)
            
            try:
                money = float(money)
                limit_money = float(limit_money)
            except (ValueError, TypeError):
                money = 0.0
                limit_money = 0.0
            
            is_in_debt = money < 0
            
            existing = db.query(Customer).filter(
                Customer.vos_instance_id == instance_id,
                Customer.account == account
            ).first()
            
            if existing:
                existing.money = money
                existing.limit_money = limit_money
                existing.is_in_debt = is_in_debt
                existing.raw_data = customer_data
                existing.synced_at = datetime.utcnow()
                updated_count += 1
            else:
                new_customer = Customer(
                    vos_instance_id=instance_id,
                    account=account,
                    money=money,
                    limit_money=limit_money,
                    is_in_debt=is_in_debt,
                    raw_data=customer_data,
                    synced_at=datetime.utcnow()
                )
                db.add(new_customer)
                synced_count += 1
        
        db.commit()
        
        logger.info(f'✅ VOS {inst.name} 客户数据同步完成: 总数={total}, 新增={synced_count}, 更新={updated_count}')
        
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
def sync_cdrs_for_single_day(instance_id: int, date_str: str):
    """
    同步单个VOS实例单天的历史话单到ClickHouse（按客户循环）

    Args:
        instance_id: VOS实例ID
        date_str: 日期字符串，格式：YYYYMMDD
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
        inst = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
        if not inst:
            logger.error(f'VOS实例 {instance_id} 未找到')
            return {'success': False, 'message': 'VOS实例未找到'}
        
        logger.info(f'📞 开始同步 VOS {inst.name} 在 {date_str} 的话单数据到 ClickHouse...')
        
        # 获取客户列表
        customers = db.query(Customer).filter(
            Customer.vos_instance_id == inst.id
        ).all()
        
        if not customers:
            logger.warning(f'VOS {inst.name} 没有客户数据，跳过话单同步')
            return {'success': True, 'total': 0, 'new': 0, 'date': date_str, 'message': '没有客户数据'}
        
        logger.info(f'  按客户同步 (共 {len(customers)} 个客户)...')
        
        # 按客户循环同步
        total_synced = 0
        client = VOSClient(inst.base_url)
        
        for idx, customer in enumerate(customers, 1):
            account = customer.account
            logger.info(f'    [{idx}/{len(customers)}] 同步客户: {account}')
            
            # 更新同步进度
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
                        'synced_count': total_synced,
                        'start_time': datetime.now().isoformat(),
                        'sync_date': date_str
                    }, ensure_ascii=False)
                )
            
            # 查询该客户的话单
            try:
                result = client.call_api('/external/server/GetCdr', {
                    'accounts': [account],
                    'beginTime': date_str,
                    'endTime': date_str
                })
                
                # VOS API可能返回数组或对象
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                
                if not isinstance(result, dict) or result.get('retCode') != 0:
                    logger.warning(f'      客户 {account} 话单查询失败')
                    # 即使失败也延迟，避免请求过快
                    if idx < len(customers):
                        time.sleep(0.5)
                    continue
                
                # 提取话单列表
                cdrs = result.get('infoCdrs') or result.get('cdrs') or result.get('CDRList') or []
                if not isinstance(cdrs, list):
                    for v in result.values():
                        if isinstance(v, list):
                            cdrs = v
                            break
                
                if cdrs:
                    inserted = ClickHouseCDR.insert_cdrs(cdrs, vos_id=inst.id, vos_uuid=str(inst.vos_uuid))
                    total_synced += inserted
                    logger.info(f'      ✅ 客户 {account}: 同步 {inserted} 条话单')
                
            except Exception as e:
                logger.exception(f'      ❌ 客户 {account} 同步失败: {e}')
                # 即使失败也延迟，避免请求过快
                if idx < len(customers):
                    time.sleep(0.5)
                continue
            
            # 每个客户之间延迟0.5秒，避免请求过于频繁导致VOS卡死
            # 最后一个客户不需要延迟
            if idx < len(customers):
                time.sleep(0.5)
        
        # 清除同步进度
        if r:
            r.delete('cdr_sync_progress')
        
        logger.info(f'✅ VOS {inst.name} 在 {date_str} 话单同步完成: 共 {total_synced} 条')
        
        return {
            'success': True,
            'total': total_synced,
            'new': total_synced,
            'date': date_str,
            'instance_name': inst.name,
            'customers_count': len(customers)
        }
    
    except Exception as e:
        logger.exception(f'同步VOS实例 {instance_id} 在 {date_str} 的话单数据时发生错误: {e}')
        # 清除同步进度（错误）
        if r:
            r.delete('cdr_sync_progress')
        return {'success': False, 'message': str(e), 'date': date_str}
    finally:
        db.close()

