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
    """
    根据统计日期和周期类型，获取查询的起始和结束日期
    
    对于月/季度/年统计，统计从周期开始到stat_date（昨天）的累计数据
    这样可以每天更新当月/当季/当年的累计统计
    """
    if period_type == 'day':
        # 日统计：统计单日数据
        start_date = stat_date
        end_date = stat_date + timedelta(days=1)
    elif period_type == 'month':
        # 月统计：从当月1日到stat_date（昨天）的累计数据
        start_date = stat_date.replace(day=1)
        end_date = stat_date + timedelta(days=1)  # 到昨天为止（包含昨天）
    elif period_type == 'quarter':
        # 季度统计：从当季第一天到stat_date（昨天）的累计数据
        quarter = (stat_date.month - 1) // 3
        start_date = date(stat_date.year, quarter * 3 + 1, 1)
        end_date = stat_date + timedelta(days=1)  # 到昨天为止（包含昨天）
    elif period_type == 'year':
        # 年度统计：从当年1月1日到stat_date（昨天）的累计数据
        start_date = date(stat_date.year, 1, 1)
        end_date = stat_date + timedelta(days=1)  # 到昨天为止（包含昨天）
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
        
        logger.info(f"📊 开始统计VOS节点 {instance.name} (ID={vos_id}, UUID={vos_uuid_str})")
        logger.info(f"   统计日期: {statistic_date}, 周期类型: {period_types}")
        
        # 检查ClickHouse中是否有数据
        try:
            check_query = f"""
                SELECT count() as total
                FROM cdrs
                WHERE vos_id = {vos_id}
                  AND vos_uuid = '{vos_uuid_str}'
                  AND toDate(start) >= toDate('{statistic_date - timedelta(days=7)}')
                  AND toDate(start) <= toDate('{statistic_date}')
            """
            ch_result = ch_db.execute(check_query)
            if ch_result and ch_result[0]:
                total_cdrs = ch_result[0][0] or 0
                logger.info(f"   ClickHouse中最近7天的话单数量: {total_cdrs}")
                if total_cdrs == 0:
                    logger.warning(f"   ⚠️ ClickHouse中没有找到话单数据，可能还没有同步话单")
        except Exception as e:
            logger.warning(f"   ⚠️ 检查ClickHouse数据时出错: {e}")
        
        results = {
            'vos_statistics': 0,
            'account_statistics': 0,
            'gateway_statistics': 0
        }
        
        for period_type in period_types:
            start_date, end_date = get_period_dates(statistic_date, period_type)
            
            logger.info(f"  📈 统计周期: {period_type}, 日期范围: {start_date} 到 {end_date}")
            
            try:
                # 1. 统计VOS节点级别
                logger.info(f"    计算VOS节点级别统计...")
                vos_stats = calculate_vos_statistics(ch_db, vos_id, vos_uuid_str, start_date, end_date, statistic_date, period_type)
                if vos_stats:
                    if vos_stats.get('total_calls', 0) > 0:
                        save_vos_statistics(db, vos_id, vos_uuid_str, statistic_date, period_type, vos_stats)
                        results['vos_statistics'] += 1
                        logger.info(f"    ✅ VOS节点统计: 通话数={vos_stats.get('total_calls', 0)}, 费用={vos_stats.get('total_fee', 0)}")
                    else:
                        logger.info(f"    ⚠️ VOS节点统计: 没有通话数据，跳过保存")
                else:
                    logger.warning(f"    ⚠️ VOS节点统计: 返回空结果")
                
                # 2. 统计账户级别
                logger.info(f"    计算账户级别统计...")
                account_stats = calculate_account_statistics(ch_db, vos_id, vos_uuid_str, start_date, end_date, statistic_date, period_type)
                account_count = len(account_stats)
                if account_count > 0:
                    for account_name, stats in account_stats.items():
                        save_account_statistics(db, vos_id, vos_uuid_str, account_name, statistic_date, period_type, stats)
                        results['account_statistics'] += 1
                    logger.info(f"    ✅ 账户统计: {account_count} 个账户")
                else:
                    logger.info(f"    ⚠️ 账户统计: 没有账户数据")
                
                # 3. 统计网关级别（对接网关和落地网关）
                logger.info(f"    计算网关级别统计...")
                gateway_stats = calculate_gateway_statistics(ch_db, vos_id, vos_uuid_str, start_date, end_date, statistic_date, period_type)
                gateway_count = len(gateway_stats)
                if gateway_count > 0:
                    for (gateway_name, gateway_type), stats in gateway_stats.items():
                        save_gateway_statistics(db, vos_id, vos_uuid_str, gateway_name, gateway_type, statistic_date, period_type, stats)
                        results['gateway_statistics'] += 1
                    logger.info(f"    ✅ 网关统计: {gateway_count} 个网关（对接+落地）")
                else:
                    logger.info(f"    ⚠️ 网关统计: 没有网关数据")
                    
            except Exception as e:
                logger.error(f"    ❌ 统计周期 {period_type} 时出错: {e}", exc_info=True)
                continue
        
        db.commit()
        logger.info(f"✅ VOS节点 {instance.name} 统计完成: {results}")
        
        return {'success': True, 'results': results}
        
    except Exception as e:
        logger.error(f"❌ 统计失败: {e}", exc_info=True)
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery.task
def calculate_cdr_statistics_with_date_range(
    vos_id: int, 
    statistic_date: date, 
    period_types: list,
    start_date: date,
    end_date: date
):
    """
    使用自定义日期范围计算指定VOS节点的话单统计
    
    用于统计完整周期的数据（如：上个月的完整数据）
    
    Args:
        vos_id: VOS实例ID
        statistic_date: 统计日期（用于存储到数据库）
        period_types: 统计周期类型列表
        start_date: 查询的起始日期
        end_date: 查询的结束日期（不包含）
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
        
        vos_uuid_str = str(instance.vos_uuid)
        
        logger.info(f"开始统计VOS节点 {instance.name} (ID={vos_id}) 的完整周期数据，日期范围={start_date} 到 {end_date}, 周期={period_types}")
        
        results = {
            'vos_statistics': 0,
            'account_statistics': 0,
            'gateway_statistics': 0
        }
        
        for period_type in period_types:
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
            
            # 3. 统计网关级别（对接网关和落地网关）
            gateway_stats = calculate_gateway_statistics(ch_db, vos_id, vos_uuid_str, start_date, end_date, statistic_date, period_type)
            for (gateway_name, gateway_type), stats in gateway_stats.items():
                save_gateway_statistics(db, vos_id, vos_uuid_str, gateway_name, gateway_type, statistic_date, period_type, stats)
                results['gateway_statistics'] += 1
        
        db.commit()
        logger.info(f"✅ VOS节点 {instance.name} 完整周期统计完成: {results}")
        
        return {'success': True, 'results': results}
        
    except Exception as e:
        logger.error(f"❌ 完整周期统计失败: {e}", exc_info=True)
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
    """统计网关级别的话单数据（同时统计对接网关和落地网关）"""
    stats_dict = {}
    try:
        # 统计落地网关（callee_gateway）
        callee_query = f"""
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
        
        result = ch_db.execute(callee_query)
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
                
                # 使用 (gateway_name, gateway_type) 作为键
                key = (gateway_name, 'callee')
                stats_dict[key] = {
                    'gateway_name': gateway_name,
                    'gateway_type': 'callee',
                    'total_calls': total_calls,
                    'connected_calls': connected_calls,
                    'total_duration': total_duration,
                    'total_fee': total_fee,
                    'connection_rate': connection_rate
                }
        
        # 统计对接网关（caller_gateway）
        caller_query = f"""
            SELECT 
                caller_gateway,
                count() as total_calls,
                countIf(hold_time > 0) as connected_calls,
                sumIf(hold_time, hold_time > 0) as total_duration,
                sum(fee) as total_fee
            FROM cdrs
            WHERE vos_id = {vos_id}
              AND vos_uuid = '{vos_uuid}'
              AND toDate(start) >= toDate('{start_date}')
              AND toDate(start) < toDate('{end_date}')
              AND caller_gateway != ''
            GROUP BY caller_gateway
        """
        
        result = ch_db.execute(caller_query)
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
                
                # 使用 (gateway_name, gateway_type) 作为键
                key = (gateway_name, 'caller')
                stats_dict[key] = {
                    'gateway_name': gateway_name,
                    'gateway_type': 'caller',
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


def save_gateway_statistics(db, vos_id: int, vos_uuid: str, gateway_name: str, gateway_type: str, stat_date: date, period_type: str, stats: dict):
    """保存网关统计（支持对接网关和落地网关）"""
    existing = db.query(GatewayCdrStatistics).filter(
        GatewayCdrStatistics.vos_id == vos_id,
        GatewayCdrStatistics.vos_uuid == vos_uuid,
        GatewayCdrStatistics.gateway_name == gateway_name,
        GatewayCdrStatistics.gateway_type == gateway_type,
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
            gateway_name=gateway_name,
            gateway_type=gateway_type,
            statistic_date=stat_date,
            period_type=period_type,
            total_fee=Decimal(str(stats['total_fee'])),
            total_duration=stats['total_duration'],
            total_calls=stats['total_calls'],
            connected_calls=stats['connected_calls'],
            connection_rate=Decimal(str(stats['connection_rate']))
        )
        db.add(existing)


def get_period_types_to_calculate(stat_date: date):
    """
    根据统计日期，智能判断需要统计哪些周期类型
    
    规则：
    1. 日统计：每天都要统计前一天的数据
    2. 月统计：每天都要统计当月1日到昨天的累计数据（进行中的月份）
    3. 季度统计：每天都要统计当季第一天到昨天的累计数据（进行中的季度）
    4. 年度统计：每天都要统计当年1月1日到昨天的累计数据（进行中的年份）
    
    注意：在特定日期还会额外统计上一个完整周期的数据：
    - 每月1日：额外统计上个月的完整数据
    - 每季度第一天：额外统计上一季度的完整数据
    - 每年1月1日：额外统计上一年的完整数据
    """
    today = date.today()
    period_types = ['day', 'month', 'quarter', 'year']  # 每天都要统计这些周期类型
    
    # 在特定日期，需要额外统计上一个完整周期的数据
    # 注意：stat_date 是 yesterday
    additional_periods = []
    
    # 如果今天是每月1日，yesterday 是上个月的最后一天，需要统计上个月的完整数据
    if today.day == 1:
        # 计算上个月的日期范围
        last_month_end = stat_date  # 上个月的最后一天
        last_month_start = last_month_end.replace(day=1)  # 上个月的第一天
        additional_periods.append({
            'type': 'month',
            'period_start': last_month_start,
            'period_end': last_month_end + timedelta(days=1),
            'stat_date': last_month_end,
            'description': f"上个月（{last_month_start.strftime('%Y年%m月')}）的完整数据"
        })
        logger.info(f"今天是每月第一天，将额外统计上个月（{last_month_start.strftime('%Y年%m月')}）的完整数据")
    
    # 如果今天是每季度第一天，yesterday 是上一季度的最后一天，需要统计上一季度的完整数据
    if today.month in [1, 4, 7, 10] and today.day == 1:
        last_quarter_end = stat_date  # 上一季度的最后一天
        last_quarter_month = ((last_quarter_end.month - 1) // 3) * 3 + 1  # 上一季度的起始月份
        last_quarter_start = date(last_quarter_end.year, last_quarter_month, 1)
        quarter_num = (last_quarter_end.month - 1) // 3 + 1
        additional_periods.append({
            'type': 'quarter',
            'period_start': last_quarter_start,
            'period_end': last_quarter_end + timedelta(days=1),
            'stat_date': last_quarter_end,
            'description': f"上一季度（{last_quarter_end.year}年第{quarter_num}季度）的完整数据"
        })
        logger.info(f"今天是季度第一天，将额外统计上一季度（{last_quarter_end.year}年第{quarter_num}季度）的完整数据")
    
    # 如果今天是每年1月1日，yesterday 是上一年的最后一天，需要统计上一年的完整数据
    if today.month == 1 and today.day == 1:
        last_year_end = stat_date  # 上一年的最后一天
        last_year_start = date(last_year_end.year, 1, 1)
        additional_periods.append({
            'type': 'year',
            'period_start': last_year_start,
            'period_end': date(last_year_end.year + 1, 1, 1),
            'stat_date': last_year_end,
            'description': f"上一年（{last_year_end.year}年）的完整数据"
        })
        logger.info(f"今天是年初第一天，将额外统计上一年（{last_year_end.year}年）的完整数据")
        logger.info(f"注意：跨年后，{last_year_end.year}年的数据将不再更新")
    
    return period_types, additional_periods


@celery.task(bind=True)
def calculate_all_instances_statistics(self):
    """
    为所有启用的VOS实例计算统计（每天凌晨2点30分执行）
    智能判断需要统计的周期类型：
    - 日统计：每天都要统计前一天的数据
    - 月统计：每天都要统计当月1日到昨天的累计数据（进行中的月份）
    - 季度统计：每天都要统计当季第一天到昨天的累计数据（进行中的季度）
    - 年度统计：每天都要统计当年1月1日到昨天的累计数据（进行中的年份）
    
    在特定日期还会额外统计上一个完整周期的数据：
    - 每月1日：额外统计上个月的完整数据
    - 每季度第一天：额外统计上一季度的完整数据
    - 每年1月1日：额外统计上一年的完整数据
    """
    logger.info("=" * 80)
    logger.info("📊 开始执行统计任务: calculate_all_instances_statistics")
    logger.info("=" * 80)
    
    db = SessionLocal()
    try:
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        logger.info(f"查询到 {len(instances)} 个启用的VOS实例")
        
        if not instances:
            logger.warning('⚠️ 没有启用的VOS实例，跳过统计任务')
            return {'success': True, 'message': '没有VOS实例需要统计', 'instances_count': 0}
        
        yesterday = date.today() - timedelta(days=1)
        logger.info(f"📅 统计日期: {yesterday}")
        
        # 智能判断需要统计的周期类型
        period_types, additional_periods = get_period_types_to_calculate(yesterday)
        logger.info(f"📈 本次统计将计算以下周期类型: {period_types}")
        if additional_periods:
            logger.info(f"📊 额外统计完整周期: {[p['description'] for p in additional_periods]}")
        
        results = []
        skipped_count = 0
        
        for inst in instances:
            logger.info(f"处理VOS实例: {inst.name} (ID={inst.id}, UUID={inst.vos_uuid})")
            
            if not inst.vos_uuid:
                logger.warning(f"⚠️ VOS实例 {inst.name} (ID={inst.id}) 没有UUID，跳过统计")
                skipped_count += 1
                continue
            
            try:
                # 1. 统计进行中的周期（当月/当季/当年）
                logger.info(f"  创建统计任务: {inst.name}, 日期={yesterday}, 周期={period_types}")
                result = calculate_cdr_statistics.delay(inst.id, yesterday, period_types)
                results.append({
                    'instance_id': inst.id,
                    'instance_name': inst.name,
                    'task_id': result.id,
                    'statistic_date': str(yesterday),
                    'period_types': period_types,
                    'type': 'current_periods'
                })
                logger.info(f"  ✅ 已创建统计任务: {inst.name} (ID={inst.id}), 任务ID={result.id}")
                
                # 2. 统计额外完整周期（如果有）
                for additional_period in additional_periods:
                    # 使用自定义日期范围统计完整周期
                    period_type = additional_period['type']
                    period_stat_date = additional_period['stat_date']
                    result = calculate_cdr_statistics_with_date_range.delay(
                        inst.id, 
                        period_stat_date, 
                        [period_type],
                        additional_period['period_start'],
                        additional_period['period_end']
                    )
                    results.append({
                        'instance_id': inst.id,
                        'instance_name': inst.name,
                        'task_id': result.id,
                        'statistic_date': str(period_stat_date),
                        'period_types': [period_type],
                        'type': 'complete_period',
                        'description': additional_period['description']
                    })
                    logger.info(f"  ✅ 已创建额外统计任务: {inst.name} (ID={inst.id}), 任务ID={result.id}")
            
            except Exception as e:
                logger.error(f"  ❌ 为VOS实例 {inst.name} (ID={inst.id}) 创建统计任务失败: {e}", exc_info=True)
                skipped_count += 1
                continue
        
        logger.info("=" * 80)
        logger.info(f"✅ 统计任务创建完成:")
        logger.info(f"   - 总实例数: {len(instances)}")
        logger.info(f"   - 成功创建任务: {len(results)}")
        logger.info(f"   - 跳过实例数: {skipped_count}")
        logger.info("=" * 80)
        
        return {
            'success': True, 
            'results': results, 
            'instances_count': len(instances),
            'tasks_created': len(results),
            'skipped_count': skipped_count
        }
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ 统计任务执行失败: {e}", exc_info=True)
        logger.error("=" * 80)
        return {'success': False, 'error': str(e)}
    finally:
        db.close()

