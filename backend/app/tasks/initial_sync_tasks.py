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
    同步单个VOS实例单天的历史话单
    
    Args:
        instance_id: VOS实例ID
        date_str: 日期字符串，格式：YYYYMMDD
    """
    db = SessionLocal()
    try:
        inst = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
        if not inst:
            logger.error(f'VOS实例 {instance_id} 未找到')
            return {'success': False, 'message': 'VOS实例未找到'}
        
        logger.info(f'📞 开始同步 VOS {inst.name} 在 {date_str} 的话单数据...')
        
        client = VOSClient(inst.base_url)
        
        # 调用VOS API获取话单
        try:
            result = client.call_api('/external/server/GetCdr', {
                'beginTime': date_str,
                'endTime': date_str
            })
        except Exception as e:
            logger.exception(f'从VOS {inst.name} 获取 {date_str} 话单数据失败: {e}')
            return {'success': False, 'message': str(e), 'date': date_str}
        
        # VOS API可能返回数组或对象
        if isinstance(result, list) and len(result) > 0:
            result = result[0]  # 取第一个元素
        
        if not isinstance(result, dict):
            logger.warning(f'VOS {inst.name} 返回的话单数据格式异常')
            return {'success': False, 'message': '返回数据格式异常', 'date': date_str}
        
        if result.get('retCode') != 0:
            error_msg = result.get('exception', '未知错误')
            logger.warning(f'VOS {inst.name} API错误 (retCode={result.get("retCode")}): {error_msg}')
            return {'success': False, 'message': error_msg, 'date': date_str}
        
        # 提取话单列表（优先使用infoCdrs）
        cdrs = result.get('infoCdrs') or result.get('cdrs') or result.get('CDRList') or []
        if not isinstance(cdrs, list):
            logger.warning(f'VOS {inst.name} 话单数据格式错误，不是列表类型')
            return {'success': False, 'message': '话单数据格式错误', 'date': date_str}
        
        if not cdrs:
            logger.info(f'VOS {inst.name} 在 {date_str} 没有话单数据')
            return {'success': True, 'total': 0, 'new': 0, 'date': date_str}
        
        total = len(cdrs)
        new_count = 0
        
        for c in cdrs:
            # 提取话单唯一标识（flowNo）- VOS返回的是整数
            flow_no = c.get('flowNo')
            if not flow_no:
                logger.warning(f'话单缺少flowNo字段，跳过: {c}')
                continue
            
            # 转换为字符串存储
            flow_no_str = str(flow_no)
            
            # 检查是否已存在（使用flowNo去重）
            exists = db.query(CDR).filter(CDR.flow_no == flow_no_str).first()
            if exists:
                continue
            
            # 提取账户信息（完全匹配VOS字段名）
            account_name = c.get('accountName', '')
            account = c.get('account', '')
            
            # 提取呼叫信息（完全匹配VOS字段名）
            caller_e164 = c.get('callerE164', '')
            callee_access_e164 = c.get('calleeAccessE164', '')
            
            # 提取时间信息（VOS返回的是毫秒时间戳）
            start_timestamp = c.get('start')  # 毫秒时间戳，如 1760922383500
            stop_timestamp = c.get('stop')
            
            # 时间戳转换（毫秒 → datetime）
            start_dt = None
            stop_dt = None
            
            if start_timestamp:
                try:
                    # 毫秒转秒，然后转datetime
                    start_dt = datetime.fromtimestamp(start_timestamp / 1000.0)
                except Exception as e:
                    logger.warning(f'start时间戳转换失败: {start_timestamp}, 错误: {e}')
            
            if stop_timestamp:
                try:
                    stop_dt = datetime.fromtimestamp(stop_timestamp / 1000.0)
                except Exception as e:
                    logger.warning(f'stop时间戳转换失败: {stop_timestamp}, 错误: {e}')
            
            # 如果start转换失败，跳过这条记录
            if not start_dt:
                logger.warning(f'话单缺少有效的start时间，跳过: flowNo={flow_no}')
                continue
            
            # 提取时长和费用（完全匹配VOS字段名）
            hold_time = c.get('holdTime', 0)
            fee_time = c.get('feeTime', 0)
            fee_value = c.get('fee', 0)
            
            # 提取终止信息（完全匹配VOS字段名）
            end_reason_raw = c.get('endReason')
            end_reason = str(end_reason_raw) if end_reason_raw is not None else ''
            
            end_direction = c.get('endDirection')
            if end_direction is not None:
                try:
                    end_direction = int(end_direction)
                except:
                    end_direction = None
            
            # 提取网关和IP（完全匹配VOS字段名）
            callee_gateway = c.get('calleeGateway', '')
            callee_ip = c.get('calleeip', '')
            
            # 创建新记录
            newc = CDR(
                vos_id=inst.id,
                account_name=account_name,
                account=account,
                caller_e164=caller_e164,
                callee_access_e164=callee_access_e164,
                start=start_dt,
                stop=stop_dt,
                hold_time=hold_time,
                fee_time=fee_time,
                fee=fee_value,
                end_reason=end_reason,
                end_direction=end_direction,
                callee_gateway=callee_gateway,
                callee_ip=callee_ip,
                raw=c,  # 保存原始JSON数据（JSONB格式）
                flow_no=flow_no_str
            )
            db.add(newc)
            new_count += 1
        
        db.commit()
        
        logger.info(f'✅ VOS {inst.name} 在 {date_str} 话单同步完成: 总数={total}, 新增={new_count}')
        
        return {
            'success': True,
            'total': total,
            'new': new_count,
            'date': date_str,
            'instance_name': inst.name
        }
        
    except Exception as e:
        logger.exception(f'同步VOS实例 {instance_id} 在 {date_str} 的话单数据时发生错误: {e}')
        db.rollback()
        return {'success': False, 'message': str(e), 'date': date_str}
    finally:
        db.close()

