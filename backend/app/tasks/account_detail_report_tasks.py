"""
账户明细报表同步任务
每天定时从VOS API获取所有账户的前一天明细报表
"""
from app.tasks.celery_app import celery
from app.core.db import SessionLocal
from app.models.vos_instance import VOSInstance
from app.models.customer import Customer
from app.models.account_detail_report import AccountDetailReport
from app.core.vos_client import VOSClient
from datetime import datetime, date, timedelta
import logging
from decimal import Decimal
import time

logger = logging.getLogger(__name__)


def convert_timestamp_to_date(timestamp_ms: int) -> date:
    """将UTC时间戳（毫秒）转换为日期"""
    return datetime.fromtimestamp(timestamp_ms / 1000).date()


def convert_date_to_timestamp_ms(target_date: date) -> int:
    """将日期转换为UTC时间戳（毫秒）"""
    dt = datetime.combine(target_date, datetime.min.time())
    return int(dt.timestamp() * 1000)


@celery.task
def check_and_run_account_detail_report_sync():
    """
    检查是否到达配置的账户明细报表同步时间，如果是则执行同步
    每分钟检查一次（精确匹配时间）
    """
    from app.models.app_config import AppConfig
    from app.core.config import settings
    import redis
    
    db = SessionLocal()
    
    try:
        # 读取配置的同步时间
        config = db.query(AppConfig).filter(
            AppConfig.config_key == 'account_detail_report_sync_time'
        ).first()
        
        if not config:
            # 默认 03:00
            configured_time = '03:00'
        else:
            configured_time = config.config_value
        
        # 解析配置的时间
        try:
            hour, minute = map(int, configured_time.split(':'))
        except ValueError:
            logger.error(f'配置的账户明细报表同步时间格式错误: {configured_time}，使用默认时间 03:00')
            hour, minute = 3, 0
        
        # 获取当前时间
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        # 判断是否到达同步时间（每分钟检查一次，精确匹配小时和分钟）
        if current_hour == hour and current_minute == minute:
            logger.info(f'⏰ 到达配置的账户明细报表同步时间 {configured_time}，开始执行自动同步')
            
            # 检查是否已有同步任务在运行（避免重复执行）
            try:
                r = redis.from_url(settings.REDIS_URL)
                if r.exists('account_detail_report_sync_lock'):
                    logger.warning('已有账户明细报表同步任务在运行，跳过本次自动同步')
                    return {'success': False, 'message': '同步任务已在运行中', 'skipped': True}
            except Exception as e:
                logger.warning(f'检查同步锁失败: {e}，继续执行')
            
            # 执行同步任务（sync_days=None 表示从数据库读取配置）
            return sync_account_detail_reports_daily(sync_days=None)
        else:
            logger.debug(f'当前时间 {current_hour:02d}:{current_minute:02d}，配置账户明细同步时间 {configured_time}，不执行同步')
            return {'success': True, 'message': '未到同步时间', 'skipped': True}
            
    except Exception as e:
        logger.exception(f'检查账户明细报表同步时间失败: {e}')
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery.task(bind=True)
def sync_account_detail_reports_daily(self, sync_days: int = None):
    """
    每天定时同步所有VOS节点上所有账户的明细报表
    
    执行时间：每天凌晨3点（在CDR统计之后）
    
    Args:
        sync_days: 同步天数（如果为None，则从数据库读取配置，默认1天）
    """
    from app.models.app_config import AppConfig
    
    db = SessionLocal()
    
    try:
        # 获取同步天数配置
        if sync_days is None:
            config = db.query(AppConfig).filter(AppConfig.config_key == 'account_detail_report_sync_days').first()
            if config and config.config_value:
                try:
                    sync_days = int(config.config_value)
                except ValueError:
                    sync_days = 1
            else:
                sync_days = 1
        
        # 确保同步天数在有效范围内
        if sync_days < 1 or sync_days > 30:
            sync_days = 1
        
        # 获取所有启用的VOS实例
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        if not instances:
            logger.info('没有启用的VOS实例，跳过账户明细报表同步任务')
            return {'success': True, 'message': '没有VOS实例需要同步', 'instances_count': 0}
        
        # 计算需要同步的日期列表
        today = date.today()
        sync_dates = [today - timedelta(days=i) for i in range(sync_days)]
        
        logger.info(f"📊 开始同步账户明细报表，同步天数: {sync_days}，日期范围: {sync_dates[-1]} 至 {sync_dates[0]}")
        logger.info(f"   共 {len(instances)} 个VOS实例需要同步")
        
        total_synced = 0
        total_errors = 0
        task_count = 0
        
        # 为每个实例和每天创建任务
        for instance in instances:
            if not instance.vos_uuid:
                logger.warning(f"VOS实例 {instance.name} (ID={instance.id}) 没有UUID，跳过")
                continue
            
            for sync_date in sync_dates:
                try:
                    # 延迟执行，避免对VOS服务器造成压力
                    countdown = task_count * 5  # 每5秒创建一个任务
                    
                    # 创建异步任务
                    sync_single_instance_account_detail_reports.apply_async(
                        args=[instance.id, sync_date],
                        countdown=countdown
                    )
                    
                    task_count += 1
                    logger.info(f"🔄 创建任务：同步VOS实例 {instance.name} (ID={instance.id}) 的账户明细报表，日期: {sync_date}，延迟: {countdown}秒")
                    
                except Exception as e:
                    logger.error(f"创建同步任务失败: {instance.name}, 日期: {sync_date}, error={e}")
                    total_errors += 1
                    continue
        
        logger.info(f"📊 账户明细报表同步任务创建完成")
        logger.info(f"   共创建 {task_count} 个任务")
        logger.info(f"   失败: {total_errors} 个任务")
        
        return {
            'success': True,
            'message': '账户明细报表同步任务已创建',
            'tasks_created': task_count,
            'error_count': total_errors,
            'instances_count': len(instances),
            'sync_days': sync_days
        }
        
    except Exception as e:
        logger.error(f"账户明细报表同步任务失败: {e}", exc_info=True)
        db.rollback()
        return {
            'success': False,
            'message': f'账户明细报表同步任务失败: {str(e)}'
        }
    finally:
        db.close()


@celery.task(bind=True)
def sync_single_instance_account_detail_reports(self, instance_id: int, target_date: date = None):
    """
    同步指定VOS实例的账户明细报表
    
    Args:
        instance_id: VOS实例ID
        target_date: 目标日期（默认昨天）
    """
    db = SessionLocal()
    
    try:
        # 获取VOS实例
        instance = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
        if not instance or not instance.enabled:
            logger.warning(f"VOS实例 {instance_id} 不存在或未启用")
            return {'success': False, 'message': 'VOS实例不存在或未启用'}
        
        if not instance.vos_uuid:
            logger.warning(f"VOS实例 {instance_id} 没有UUID")
            return {'success': False, 'message': 'VOS实例没有UUID'}
        
        # 默认统计昨天
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        begin_time_str = target_date.strftime('%Y%m%d')
        end_time_str = target_date.strftime('%Y%m%d')
        
        logger.info(f"🔄 同步VOS实例 {instance.name} (ID={instance_id}) 的账户明细报表，日期: {target_date}")
        
        # 获取该实例的所有账户
        customers = db.query(Customer).filter(
            Customer.vos_instance_id == instance.id,
            Customer.vos_uuid == instance.vos_uuid
        ).all()
        
        if not customers:
            logger.warning(f"VOS实例 {instance.name} 没有账户数据")
            return {'success': False, 'message': '没有账户数据'}
        
        # 获取账户列表
        account_list = [c.account for c in customers if c.account]
        if not account_list:
            logger.warning(f"VOS实例 {instance.name} 没有有效的账户号码")
            return {'success': False, 'message': '没有有效的账户号码'}
        
        logger.info(f"   共 {len(account_list)} 个账户需要同步")
        
        # 创建VOS客户端
        client = VOSClient(instance.base_url, timeout=60)  # 增加超时时间到60秒
        
        # 分批处理账户（每批50个账户，避免一次性发送太多导致超时）
        batch_size = 50
        all_reports = []
        
        for i in range(0, len(account_list), batch_size):
            batch_accounts = account_list[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(account_list) + batch_size - 1) // batch_size
            
            logger.info(f"   处理第 {batch_num}/{total_batches} 批账户（{len(batch_accounts)} 个账户）")
            
            try:
                # 调用VOS API获取账户明细报表
                payload = {
                    'accounts': batch_accounts,
                    'period': 1,  # 1=天
                    'beginTime': begin_time_str,
                    'endTime': end_time_str
                }
                
                result = client.post('/external/server/GetReportCustomerFee', payload)
                
                if not client.is_success(result):
                    error_msg = client.get_error_message(result)
                    logger.error(f"VOS API调用失败: {instance.name}, 批次 {batch_num}, {error_msg}")
                    continue
                
                # 提取数据
                batch_reports = result.get('infoReportCustomerFees', [])
                if batch_reports:
                    all_reports.extend(batch_reports)
                    logger.info(f"   批次 {batch_num} 获取到 {len(batch_reports)} 条账户明细报表数据")
                
                # 延迟1秒，避免对VOS服务器造成压力
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"处理账户批次失败: {instance.name}, 批次 {batch_num}, error={e}")
                continue
        
        if not all_reports:
            logger.warning(f"VOS实例 {instance.name} 没有返回账户明细报表数据")
            return {'success': True, 'message': '没有返回数据', 'reports_count': 0}
        
        logger.info(f"   共获取到 {len(all_reports)} 条账户明细报表数据")
        
        # 保存数据到数据库
        saved_count = 0
        for report_data in all_reports:
            try:
                # 提取字段
                account = report_data.get('account', '')
                if not account:
                    continue
                
                account_name = report_data.get('accountName', '')
                begin_time = report_data.get('beginTime', 0)
                end_time = report_data.get('endTime', 0)
                cdr_count = report_data.get('cdrCount', 0)
                total_fee = report_data.get('totalFee', 0)
                total_time = report_data.get('totalTime', 0)
                total_suite_fee = report_data.get('totalSuiteFee', 0)
                total_suite_fee_time = report_data.get('totalSuiteFeeTime', 0)
                net_fee = report_data.get('netFee', 0)
                net_time = report_data.get('netTime', 0)
                net_count = report_data.get('netCount', 0)
                local_fee = report_data.get('localFee', 0)
                local_time = report_data.get('localTime', 0)
                local_count = report_data.get('localCount', 0)
                domestic_fee = report_data.get('domesticFee', 0)
                domestic_time = report_data.get('domesticTime', 0)
                domestic_count = report_data.get('domesticCount', 0)
                international_fee = report_data.get('internationalFee', 0)
                international_time = report_data.get('internationalTime', 0)
                international_count = report_data.get('internationalCount', 0)
                
                # 检查是否已存在
                existing = db.query(AccountDetailReport).filter(
                    AccountDetailReport.vos_instance_id == instance.id,
                    AccountDetailReport.vos_uuid == instance.vos_uuid,
                    AccountDetailReport.account == account,
                    AccountDetailReport.begin_time == begin_time,
                    AccountDetailReport.end_time == end_time
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.account_name = account_name
                    existing.cdr_count = cdr_count
                    existing.total_fee = Decimal(str(total_fee))
                    existing.total_time = total_time
                    existing.total_suite_fee = Decimal(str(total_suite_fee))
                    existing.total_suite_fee_time = total_suite_fee_time
                    existing.net_fee = Decimal(str(net_fee))
                    existing.net_time = net_time
                    existing.net_count = net_count
                    existing.local_fee = Decimal(str(local_fee))
                    existing.local_time = local_time
                    existing.local_count = local_count
                    existing.domestic_fee = Decimal(str(domestic_fee))
                    existing.domestic_time = domestic_time
                    existing.domestic_count = domestic_count
                    existing.international_fee = Decimal(str(international_fee))
                    existing.international_time = international_time
                    existing.international_count = international_count
                    existing.updated_at = datetime.utcnow()
                else:
                    # 创建新记录
                    new_report = AccountDetailReport(
                        vos_instance_id=instance.id,
                        vos_uuid=instance.vos_uuid,
                        account=account,
                        account_name=account_name,
                        begin_time=begin_time,
                        end_time=end_time,
                        cdr_count=cdr_count,
                        total_fee=Decimal(str(total_fee)),
                        total_time=total_time,
                        total_suite_fee=Decimal(str(total_suite_fee)),
                        total_suite_fee_time=total_suite_fee_time,
                        net_fee=Decimal(str(net_fee)),
                        net_time=net_time,
                        net_count=net_count,
                        local_fee=Decimal(str(local_fee)),
                        local_time=local_time,
                        local_count=local_count,
                        domestic_fee=Decimal(str(domestic_fee)),
                        domestic_time=domestic_time,
                        domestic_count=domestic_count,
                        international_fee=Decimal(str(international_fee)),
                        international_time=international_time,
                        international_count=international_count
                    )
                    db.add(new_report)
                
                saved_count += 1
                
            except Exception as e:
                logger.error(f"保存账户明细报表数据失败: {instance.name}, account={account}, error={e}")
                continue
        
        # 提交事务
        db.commit()
        logger.info(f"✅ VOS实例 {instance.name} 同步完成，保存了 {saved_count} 条记录")
        
        return {
            'success': True,
            'message': '账户明细报表同步完成',
            'synced_count': saved_count,
            'instance_id': instance_id,
            'instance_name': instance.name
        }
        
    except Exception as e:
        logger.error(f"同步账户明细报表失败: {e}", exc_info=True)
        db.rollback()
        return {
            'success': False,
            'message': f'同步失败: {str(e)}'
        }
    finally:
        db.close()

