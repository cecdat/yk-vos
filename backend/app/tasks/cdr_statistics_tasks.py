"""
话单费用统计任务
从ClickHouse统计数据并写入PostgreSQL
"""
from app.tasks.celery_app import celery
from app.core.db import SessionLocal
from app.models.vos_instance import VOSInstance
from app.models.cdr_statistics import VOSCdrStatistics, AccountCdrStatistics, GatewayCdrStatistics
from app.core.clickhouse_db import get_clickhouse_db
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def get_period_dates(stat_date: date, period_type: str):
    """根据统计日期和周期类型，获取查询的起始和结束日期"""
    if period_type == 'day':
        start_date = stat_date
        end_date = stat_date + timedelta(days=1)
    elif period_type == 'month':
        start_date = stat_date.replace(day=1)
        end_date = (start_date + relativedelta(months=1))
    elif period_type == 'quarter':
        quarter = (stat_date.month - 1) // 3
        start_date = date(stat_date.year, quarter * 3 + 1, 1)
        end_date = (start_date + relativedelta(months=3))
    elif period_type == 'year':
        start_date = date(stat_date.year, 1, 1)
        end_date = date(stat_date.year + 1, 1, 1)
    else:
        raise ValueError(f"Unsupported period_type: {period_type}")
    
    return start_date, end_date


def calculate_connection_rate(total_calls: int, connected_calls: int) -> float:
    """计算接通率（百分比）"""
    if total_calls == 0:
        return 0.0
    return round((connected_calls / total_calls) * 100, 2)


@celery.task
def calculate_cdr_statistics(vos_id: int, statistic_date: date = None, period_types: list = None):
    """
    计算指定VOS节点的话单统计
    
    Args:
        vos_id: VOS实例ID
        statistic_date: 统计日期（默认昨天）
        period_types: 统计周期类型列表（默认['day']）
    """
    db = SessionLocal()
    ch_db = get_clickhouse_db()
    
    try:
        # 获取VOS实例
        instance = db.query(VOSInstance).filter(VOSInstance.id == vos_id).first()
        if not instance or not instance.enabled:
            logger.warning(f"VOS实例 {vos_id} 不存在或未启用")
            return {'success': False, 'message': 'VOS实例不存在或未启用'}
        
        if not instance.vos_uuid:
            logger.warning(f"VOS实例 {vos_id} 没有UUID")
            return {'success': False, 'message': 'VOS实例没有UUID'}
        
        # 默认统计昨天
        if statistic_date is None:
            statistic_date = date.today() - timedelta(days=1)
        
        # 默认统计日级别
        if period_types is None:
            period_types = ['day']
        
        vos_uuid_str = str(instance.vos_uuid)
        
        logger.info(f"开始统计VOS节点 {instance.name} (ID={vos_id}, UUID={vos_uuid_str}) 的话单数据，日期={statistic_date}, 周期={period_types}")
        
        results = {
            'vos_statistics': 0,
            'account_statistics': 0,
            'gateway_statistics': 0
        }
        
        for period_type in period_types:
            start_date, end_date = get_period_dates(statistic_date, period_type)
            
            logger.info(f"  统计周期: {period_type}, 日期范围: {start_date} 到 {end_date}")
            
            # 1. 统计VOS节点级别
            vos_stats = calculate_vos_statistics(ch_db, vos_id, vos_uuid_str, start_date, end_date, statistic_date, period_type)
            if vos_stats:
                save_vos_statistics(db, vos_id, vos_uuid_str, statistic_date, period_type, vos_stats)
                results['vos_statistics'] += 1
            
            # 2. 统计账户级别
            account_stats = calculate_account_statistics(ch_db, vos_id, vos_uuid_str, start_date, end_date, statistic_date, period_type)
            for account_name, stats in account_stats.items():
                save_account_statistics(db, vos_id, vos_uuid_str, account_name, statistic_date, period_type, stats)
                results['account_statistics'] += 1
            
            # 3. 统计网关级别
            gateway_stats = calculate_gateway_statistics(ch_db, vos_id, vos_uuid_str, start_date, end_date, statistic_date, period_type)
            for gateway_name, stats in gateway_stats.items():
                save_gateway_statistics(db, vos_id, vos_uuid_str, gateway_name, statistic_date, period_type, stats)
                results['gateway_statistics'] += 1
        
        db.commit()
        logger.info(f"✅ VOS节点 {instance.name} 统计完成: {results}")
        
        return {'success': True, 'results': results}
        
    except Exception as e:
        logger.error(f"❌ 统计失败: {e}", exc_info=True)
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def calculate_vos_statistics(ch_db, vos_id: int, vos_uuid: str, start_date: date, end_date: date, stat_date: date, period_type: str):
    """统计VOS节点级别的话单数据"""
    try:
        query = f"""
            SELECT 
                count() as total_calls,
                countIf(hold_time > 0) as connected_calls,
                sumIf(hold_time, hold_time > 0) as total_duration,
                sum(fee) as total_fee
            FROM cdrs
            WHERE vos_id = {vos_id}
              AND vos_uuid = '{vos_uuid}'
              AND toDate(start) >= toDate('{start_date}')
              AND toDate(start) < toDate('{end_date}')
        """
        
        result = ch_db.execute(query)
        if result and result[0]:
            row = result[0]
            total_calls = row[0] or 0
            connected_calls = row[1] or 0
            total_duration = row[2] or 0
            total_fee = float(row[3] or 0)
            
            connection_rate = calculate_connection_rate(total_calls, connected_calls)
            
            return {
                'total_calls': total_calls,
                'connected_calls': connected_calls,
                'total_duration': total_duration,
                'total_fee': total_fee,
                'connection_rate': connection_rate
            }
    except Exception as e:
        logger.error(f"统计VOS节点级别数据失败: {e}")
    return None


def calculate_account_statistics(ch_db, vos_id: int, vos_uuid: str, start_date: date, end_date: date, stat_date: date, period_type: str):
    """统计账户级别的话单数据"""
    stats_dict = {}
    try:
        query = f"""
            SELECT 
                account_name,
                count() as total_calls,
                countIf(hold_time > 0) as connected_calls,
                sumIf(hold_time, hold_time > 0) as total_duration,
                sum(fee) as total_fee
            FROM cdrs
            WHERE vos_id = {vos_id}
              AND vos_uuid = '{vos_uuid}'
              AND toDate(start) >= toDate('{start_date}')
              AND toDate(start) < toDate('{end_date}')
              AND account_name != ''
            GROUP BY account_name
        """
        
        result = ch_db.execute(query)
        if result:
            for row in result:
                account_name = row[0] or ''
                if not account_name:
                    continue
                
                total_calls = row[1] or 0
                connected_calls = row[2] or 0
                total_duration = row[3] or 0
                total_fee = float(row[4] or 0)
                
                connection_rate = calculate_connection_rate(total_calls, connected_calls)
                
                stats_dict[account_name] = {
                    'total_calls': total_calls,
                    'connected_calls': connected_calls,
                    'total_duration': total_duration,
                    'total_fee': total_fee,
                    'connection_rate': connection_rate
                }
    except Exception as e:
        logger.error(f"统计账户级别数据失败: {e}")
    return stats_dict


def calculate_gateway_statistics(ch_db, vos_id: int, vos_uuid: str, start_date: date, end_date: date, stat_date: date, period_type: str):
    """统计网关级别的话单数据"""
    stats_dict = {}
    try:
        query = f"""
            SELECT 
                callee_gateway,
                count() as total_calls,
                countIf(hold_time > 0) as connected_calls,
                sumIf(hold_time, hold_time > 0) as total_duration,
                sum(fee) as total_fee
            FROM cdrs
            WHERE vos_id = {vos_id}
              AND vos_uuid = '{vos_uuid}'
              AND toDate(start) >= toDate('{start_date}')
              AND toDate(start) < toDate('{end_date}')
              AND callee_gateway != ''
            GROUP BY callee_gateway
        """
        
        result = ch_db.execute(query)
        if result:
            for row in result:
                gateway_name = row[0] or ''
                if not gateway_name:
                    continue
                
                total_calls = row[1] or 0
                connected_calls = row[2] or 0
                total_duration = row[3] or 0
                total_fee = float(row[4] or 0)
                
                connection_rate = calculate_connection_rate(total_calls, connected_calls)
                
                stats_dict[gateway_name] = {
                    'total_calls': total_calls,
                    'connected_calls': connected_calls,
                    'total_duration': total_duration,
                    'total_fee': total_fee,
                    'connection_rate': connection_rate
                }
    except Exception as e:
        logger.error(f"统计网关级别数据失败: {e}")
    return stats_dict


def save_vos_statistics(db, vos_id: int, vos_uuid: str, stat_date: date, period_type: str, stats: dict):
    """保存VOS节点统计"""
    existing = db.query(VOSCdrStatistics).filter(
        VOSCdrStatistics.vos_id == vos_id,
        VOSCdrStatistics.vos_uuid == vos_uuid,
        VOSCdrStatistics.statistic_date == stat_date,
        VOSCdrStatistics.period_type == period_type
    ).first()
    
    if existing:
        existing.total_fee = Decimal(str(stats['total_fee']))
        existing.total_duration = stats['total_duration']
        existing.total_calls = stats['total_calls']
        existing.connected_calls = stats['connected_calls']
        existing.connection_rate = Decimal(str(stats['connection_rate']))
        existing.updated_at = datetime.utcnow()
    else:
        from app.models.vos_instance import VOSInstance
        import uuid
        existing = VOSCdrStatistics(
            vos_id=vos_id,
            vos_uuid=uuid.UUID(vos_uuid),
            statistic_date=stat_date,
            period_type=period_type,
            total_fee=Decimal(str(stats['total_fee'])),
            total_duration=stats['total_duration'],
            total_calls=stats['total_calls'],
            connected_calls=stats['connected_calls'],
            connection_rate=Decimal(str(stats['connection_rate']))
        )
        db.add(existing)


def save_account_statistics(db, vos_id: int, vos_uuid: str, account_name: str, stat_date: date, period_type: str, stats: dict):
    """保存账户统计"""
    existing = db.query(AccountCdrStatistics).filter(
        AccountCdrStatistics.vos_id == vos_id,
        AccountCdrStatistics.vos_uuid == vos_uuid,
        AccountCdrStatistics.account_name == account_name,
        AccountCdrStatistics.statistic_date == stat_date,
        AccountCdrStatistics.period_type == period_type
    ).first()
    
    if existing:
        existing.total_fee = Decimal(str(stats['total_fee']))
        existing.total_duration = stats['total_duration']
        existing.total_calls = stats['total_calls']
        existing.connected_calls = stats['connected_calls']
        existing.connection_rate = Decimal(str(stats['connection_rate']))
        existing.updated_at = datetime.utcnow()
    else:
        import uuid
        existing = AccountCdrStatistics(
            vos_id=vos_id,
            vos_uuid=uuid.UUID(vos_uuid),
            account_name=account_name,
            statistic_date=stat_date,
            period_type=period_type,
            total_fee=Decimal(str(stats['total_fee'])),
            total_duration=stats['total_duration'],
            total_calls=stats['total_calls'],
            connected_calls=stats['connected_calls'],
            connection_rate=Decimal(str(stats['connection_rate']))
        )
        db.add(existing)


def save_gateway_statistics(db, vos_id: int, vos_uuid: str, gateway_name: str, stat_date: date, period_type: str, stats: dict):
    """保存网关统计"""
    existing = db.query(GatewayCdrStatistics).filter(
        GatewayCdrStatistics.vos_id == vos_id,
        GatewayCdrStatistics.vos_uuid == vos_uuid,
        GatewayCdrStatistics.callee_gateway == gateway_name,
        GatewayCdrStatistics.statistic_date == stat_date,
        GatewayCdrStatistics.period_type == period_type
    ).first()
    
    if existing:
        existing.total_fee = Decimal(str(stats['total_fee']))
        existing.total_duration = stats['total_duration']
        existing.total_calls = stats['total_calls']
        existing.connected_calls = stats['connected_calls']
        existing.connection_rate = Decimal(str(stats['connection_rate']))
        existing.updated_at = datetime.utcnow()
    else:
        import uuid
        existing = GatewayCdrStatistics(
            vos_id=vos_id,
            vos_uuid=uuid.UUID(vos_uuid),
            callee_gateway=gateway_name,
            statistic_date=stat_date,
            period_type=period_type,
            total_fee=Decimal(str(stats['total_fee'])),
            total_duration=stats['total_duration'],
            total_calls=stats['total_calls'],
            connected_calls=stats['connected_calls'],
            connection_rate=Decimal(str(stats['connection_rate']))
        )
        db.add(existing)


@celery.task
def calculate_all_instances_statistics():
    """为所有启用的VOS实例计算统计（每天凌晨2点执行）"""
    db = SessionLocal()
    try:
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        if not instances:
            logger.info('没有启用的VOS实例，跳过统计任务')
            return {'success': True, 'message': '没有VOS实例需要统计', 'instances_count': 0}
        
        yesterday = date.today() - timedelta(days=1)
        results = []
        
        for inst in instances:
            if inst.vos_uuid:
                # 统计昨天的日级别数据
                result = calculate_cdr_statistics.delay(inst.id, yesterday, ['day'])
                results.append({
                    'instance_id': inst.id,
                    'instance_name': inst.name,
                    'task_id': result.id
                })
                logger.info(f"已创建统计任务: {inst.name} (ID={inst.id})")
        
        return {
            'success': True,
            'instances_count': len(instances),
            'results': results
        }
    except Exception as e:
        logger.error(f"创建统计任务失败: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}
    finally:
        db.close()

