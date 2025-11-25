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
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """
    获取财务明细收支报表 (按天汇总)
    目前主要展示收入 (Total Fee)
    """
    # 默认查询最近30天
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
        
    cache_key = f'financial_income_expense_{start_date}_{end_date}_{vos_id}'
    cached_data = RedisCache.get(cache_key)
    if cached_data:
        return cached_data
        
    try:
        # 1. 获取所有客户账号（用于计算收入）
        customer_query = db.query(Customer.account).filter(Customer.account != None)
        if vos_id:
            customer_query = customer_query.filter(Customer.vos_instance_id == vos_id)
        customer_accounts = [r[0] for r in customer_query.all()]
        
        # 2. 获取所有落地网关账号（用于计算支出）
        gateway_query = db.query(Gateway.account).filter(
            Gateway.gateway_type == 'routing',
            Gateway.account != None
        )
        if vos_id:
            gateway_query = gateway_query.filter(Gateway.vos_instance_id == vos_id)
        gateway_accounts = [r[0] for r in gateway_query.all()]
        
        # 3. 查询每日统计数据
        # 由于 ClickHouse 的 cdrs_daily_stats 已经按账户聚合，我们可以直接查询
        # 但为了区分收入和支出，我们需要分别查询或一次性查询后在内存处理
        # 考虑到数据量，我们在 SQL 中做区分可能更高效，但 ClickHouse 不直接支持 IN (大列表)
        # 所以我们分别查询收入和支出
        
        from app.core.clickhouse_db import get_clickhouse_db
        ch_db = get_clickhouse_db()
        
        # 格式化日期
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # 查询收入 (Income) - 匹配客户账号
        income_data = {}
        if customer_accounts:
            # 处理账号列表，转义单引号
            cust_acc_str = "', '".join([acc.replace("'", "\\'") for acc in customer_accounts])
            income_sql = f"""
                SELECT 
                    call_date,
                    sum(total_fee) as income,
                    sum(total_duration) as duration,
                    sum(call_count) as calls
                FROM cdrs_daily_stats
                WHERE call_date >= '{start_str}' AND call_date <= '{end_str}'
                  AND account IN ('{cust_acc_str}')
                {f"AND vos_id = {vos_id}" if vos_id else ""}
                GROUP BY call_date
            """
            try:
                income_rows = ch_db.execute(income_sql)
                for row in income_rows:
                    date_key = row[0].strftime('%Y-%m-%d')
                    income_data[date_key] = {
                        'income': float(row[1]),
                        'duration': row[2],
                        'calls': row[3]
                    }
            except Exception as e:
                logger.error(f"查询收入失败: {e}")

        # 查询支出 (Expense) - 匹配落地网关账号
        expense_data = {}
        if gateway_accounts:
            # 处理账号列表，转义单引号
            gw_acc_str = "', '".join([acc.replace("'", "\\'") for acc in gateway_accounts])
            expense_sql = f"""
                SELECT 
                    call_date,
                    sum(total_fee) as expense
                FROM cdrs_daily_stats
                WHERE call_date >= '{start_str}' AND call_date <= '{end_str}'
                  AND account IN ('{gw_acc_str}')
                {f"AND vos_id = {vos_id}" if vos_id else ""}
                GROUP BY call_date
            """
            try:
                expense_rows = ch_db.execute(expense_sql)
                for row in expense_rows:
                    date_key = row[0].strftime('%Y-%m-%d')
                    expense_data[date_key] = float(row[1])
            except Exception as e:
                logger.error(f"查询支出失败: {e}")
        
        # 合并数据
        data = []
        # 生成日期范围
        current = start_date
        while current <= end_date:
            date_key = current.strftime('%Y-%m-%d')
            inc_info = income_data.get(date_key, {'income': 0, 'duration': 0, 'calls': 0})
            exp_val = expense_data.get(date_key, 0)
            
            data.append({
                'date': date_key,
                'income': inc_info['income'],
                'expense': exp_val,
                'profit': inc_info['income'] - exp_val,
                'duration': inc_info['duration'],
                'calls': inc_info['calls']
            })
            current += timedelta(days=1)
            
        # 按日期倒序
        data.sort(key=lambda x: x['date'], reverse=True)
            
        response = {'data': data}
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
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """
    获取对接账户每日明细 (Mapping/Caller Gateway)
    """
    return await _get_gateway_daily_report(db, 'caller', start_date, end_date, vos_id, gateway_name)

@router.get('/routing-daily')
async def get_routing_daily_report(
    start_date: Optional[date] = Query(None, description='开始日期'),
    end_date: Optional[date] = Query(None, description='结束日期'),
    vos_id: Optional[int] = Query(None, description='VOS实例ID'),
    gateway_name: Optional[str] = Query(None, description='网关名称'),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """
    获取落地账户每日明细 (Routing/Callee Gateway)
    """
    return await _get_gateway_daily_report(db, 'callee', start_date, end_date, vos_id, gateway_name)

async def _get_gateway_daily_report(
    db: Session,
    gateway_type: str,
    start_date: Optional[date],
    end_date: Optional[date],
    vos_id: Optional[int],
    gateway_name: Optional[str]
):
    # 默认查询最近30天
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
        
    cache_key = f'financial_gateway_{gateway_type}_{start_date}_{end_date}_{vos_id}_{gateway_name}'
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
            
        # 按日期和网关名排序
        results = query.order_by(
            desc(GatewayCdrStatistics.statistic_date),
            GatewayCdrStatistics.gateway_name
        ).limit(2000).all() # 限制返回数量防止过大
        
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
            
        response = {'data': data}
        RedisCache.set(cache_key, response, ttl=300)
        return response
        
    except Exception as e:
        logger.error(f"获取网关报表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
