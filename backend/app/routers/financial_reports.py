from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, datetime, timedelta

from app.core.db import get_db
from app.core.redis_cache import RedisCache
from app.models.user import User
from app.models.vos_instance import VOSInstance
from app.models.customer import Customer
from app.models.gateway import Gateway
from app.models.cdr_statistics import VOSCdrStatistics, GatewayCdrStatistics
from app.routers.auth import get_current_user
import logging

router = APIRouter(prefix='/financial', tags=['财务报表'])
logger = logging.getLogger(__name__)

@router.get('/income-expense')
async def get_income_expense_report(
    start_date: Optional[date] = Query(None, description='开始日期'),
    end_date: Optional[date] = Query(None, description='结束日期'),
    vos_id: Optional[int] = Query(None, description='VOS实例ID'),
    period_type: str = Query('day', description='聚合类型: day/month/quarter/year'),
    page: int = Query(1, ge=1, description='页码'),
    page_size: int = Query(25, ge=1, le=100, description='每页数量'),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """
    获取财务明细收支报表
    收入 = 对接网关（caller_gateway）消耗
    支出 = 落地网关（callee_gateway）消耗
    利润 = 收入 - 支出
    """
    # 默认查询最近7天
    if not start_date:
        start_date = date.today() - timedelta(days=7)
    if not end_date:
        end_date = date.today()
        
    cache_key = f'financial_income_expense_{start_date}_{end_date}_{vos_id}_{period_type}_{page}_{page_size}'
    cached_data = RedisCache.get(cache_key)
    if cached_data:
        return cached_data
        
    try:
        from app.core.clickhouse_db import get_clickhouse_db
        ch_db = get_clickhouse_db()
        
        # 格式化日期
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # 根据 period_type 确定分组字段
        if period_type == 'month':
            date_group = "toStartOfMonth(start)"
            date_format = "toString(toStartOfMonth(start))"  # 使用 toString 代替 formatDateTime
        elif period_type == 'quarter':
            date_group = "toStartOfQuarter(start)"
            date_format = "concat(toString(toYear(toStartOfQuarter(start))), '-Q', toString(toQuarter(start)))"
        elif period_type == 'year':
            date_group = "toStartOfYear(start)"
            date_format = "toString(toYear(toStartOfYear(start)))"
        else:  # day
            date_group = "toDate(start)"
            date_format = "toString(toDate(start))"
        
        # 查询收入（对接网关）和支出（落地网关）
        # 按账户号码分组，每个账户一条记录
        sql = f"""
            WITH income_data AS (
                SELECT 
                    {date_group} as period,
                    {date_format} as period_str,
                    account,
                    account_name,
                    groupArray(DISTINCT caller_gateway) as gateways,
                    sum(fee) as amount,
                    sum(hold_time) as duration,
                    count(*) as cdr_count
                FROM cdrs
                WHERE start >= '{start_str}' AND start < '{end_str} 23:59:59'
                  AND caller_gateway != ''
                  {f"AND vos_id = {vos_id}" if vos_id else ""}
                GROUP BY period, period_str, account, account_name
            ),
            expense_data AS (
                SELECT 
                    {date_group} as period,
                    {date_format} as period_str,
                    account,
                    account_name,
                    groupArray(DISTINCT callee_gateway) as gateways,
                    sum(fee) as amount,
                    sum(hold_time) as duration,
                    count(*) as cdr_count
                FROM cdrs
                WHERE start >= '{start_str}' AND start < '{end_str} 23:59:59'
                  AND callee_gateway != ''
                  {f"AND vos_id = {vos_id}" if vos_id else ""}
                GROUP BY period, period_str, account, account_name
            )
            SELECT 
                period_str,
                account,
                account_name,
                sum(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                sum(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense,
                sum(CASE WHEN type = 'income' THEN cdr_count ELSE 0 END) as income_cdr_count,
                sum(CASE WHEN type = 'expense' THEN cdr_count ELSE 0 END) as expense_cdr_count,
                groupArray(CASE WHEN type = 'income' THEN arrayJoin(gateways) ELSE NULL END) as caller_gateways,
                groupArray(CASE WHEN type = 'expense' THEN arrayJoin(gateways) ELSE NULL END) as callee_gateways
            FROM (
                SELECT period, period_str, account, account_name, gateways, amount, duration, cdr_count, 'income' as type
                FROM income_data
                UNION ALL
                SELECT period, period_str, account, account_name, gateways, amount, duration, cdr_count, 'expense' as type
                FROM expense_data
            )
            GROUP BY period_str, account, account_name
            ORDER BY period_str DESC, account
        """
        
        rows = ch_db.execute(sql)
        
        # 处理数据
        all_data = []
        for row in rows:
            # 过滤掉 None 值并去重
            caller_gateways = list(set([g for g in row[7] if g]))
            callee_gateways = list(set([g for g in row[8] if g]))
            
            all_data.append({
                'date': row[0],
                'account': row[1] or '',
                'account_name': row[2] or '',
                'income': float(row[3]),
                'expense': float(row[4]),
                'profit': float(row[3]) - float(row[4]),
                'income_cdr_count': row[5],
                'expense_cdr_count': row[6],
                'total_cdr_count': row[5] + row[6],
                'caller_gateways': ', '.join(caller_gateways),
                'callee_gateways': ', '.join(callee_gateways)
            })
        
        # 分页
        total = len(all_data)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        data = all_data[start_idx:end_idx]
            
        response = {
            'data': data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
        RedisCache.set(cache_key, response, ttl=300)
        return response
        
    except Exception as e:
        logger.error(f"获取财务收支报表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/mapping-daily')
async def get_mapping_daily_report(
    start_date: Optional[date] = Query(None, description='开始日期'),
    end_date: Optional[date] = Query(None, description='结束日期'),
    vos_id: Optional[int] = Query(None, description='VOS实例ID'),
    gateway_name: Optional[str] = Query(None, description='网关名称'),
    page: int = Query(1, ge=1, description='页码'),
    page_size: int = Query(25, ge=1, le=100, description='每页数量'),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """
    获取对接账户明细 (Mapping/Caller Gateway)
    """
    return await _get_gateway_daily_report(db, 'caller', start_date, end_date, vos_id, gateway_name, page, page_size)


@router.get('/routing-daily')
async def get_routing_daily_report(
    start_date: Optional[date] = Query(None, description='开始日期'),
    end_date: Optional[date] = Query(None, description='结束日期'),
    vos_id: Optional[int] = Query(None, description='VOS实例ID'),
    gateway_name: Optional[str] = Query(None, description='网关名称'),
    page: int = Query(1, ge=1, description='页码'),
    page_size: int = Query(25, ge=1, le=100, description='每页数量'),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """
    获取落地账户明细 (Routing/Callee Gateway)
    """
    return await _get_gateway_daily_report(db, 'callee', start_date, end_date, vos_id, gateway_name, page, page_size)


async def _get_gateway_daily_report(
    db: Session,
    gateway_type: str,
    start_date: Optional[date],
    end_date: Optional[date],
    vos_id: Optional[int],
    gateway_name: Optional[str],
    page: int = 1,
    page_size: int = 25
):
    # 默认查询最近30天
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
        
    cache_key = f'financial_gateway_{gateway_type}_{start_date}_{end_date}_{vos_id}_{gateway_name}_{page}_{page_size}'
    cached_data = RedisCache.get(cache_key)
    if cached_data:
        return cached_data
        
    try:
        query = db.query(GatewayCdrStatistics).filter(
            GatewayCdrStatistics.gateway_type == gateway_type,
            GatewayCdrStatistics.period_type == 'day',
            GatewayCdrStatistics.statistic_date >= start_date,
            GatewayCdrStatistics.statistic_date <= end_date
        )
        
        if vos_id:
            query = query.filter(GatewayCdrStatistics.vos_id == vos_id)
        if gateway_name:
            query = query.filter(GatewayCdrStatistics.gateway_name.ilike(f"%{gateway_name}%"))
            
        # 获取总数
        total = query.count()
        
        # 按日期和网关名排序，并分页
        results = query.order_by(
            desc(GatewayCdrStatistics.statistic_date),
            GatewayCdrStatistics.gateway_name
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        data = []
        for row in results:
            data.append({
                'date': row.statistic_date.isoformat(),
                'gateway_name': row.gateway_name,
                'total_fee': float(row.total_fee or 0),
                'total_duration': row.total_duration,
                'total_calls': row.total_calls,
                'connected_calls': row.connected_calls,
                'connection_rate': float(row.connection_rate or 0)
            })
            
        response = {
            'data': data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
        RedisCache.set(cache_key, response, ttl=300)
        return response
        
    except Exception as e:
        logger.error(f"获取网关报表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
