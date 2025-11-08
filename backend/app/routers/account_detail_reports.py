"""
账户明细报表API路由
"""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timezone

from app.core.db import get_db
from app.core.redis_cache import RedisCache
from app.models.user import User
from app.models.vos_instance import VOSInstance
from app.models.account_detail_report import AccountDetailReport
from app.routers.auth import get_current_user

router = APIRouter(prefix='/vos', tags=['账户明细报表'])
logger = logging.getLogger(__name__)


@router.get('/instances/{instance_id}/account-detail-reports')
async def get_account_detail_reports(
    instance_id: int,
    start_date: Optional[str] = Query(None, description='开始日期 YYYY-MM-DD'),
    end_date: Optional[str] = Query(None, description='结束日期 YYYY-MM-DD'),
    account: Optional[str] = Query(None, description='账户号码（可选）'),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """
    查询账户明细报表
    
    Args:
        instance_id: VOS实例ID
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        account: 账户号码（可选，留空查询所有账户）
    """
    # Redis缓存键
    cache_key = f'account_detail_reports_{instance_id}_{start_date or "all"}_{end_date or "all"}_{account or "all"}'
    
    # 尝试从Redis缓存读取（缓存5分钟）
    cached_data = RedisCache.get(cache_key)
    if cached_data is not None:
        logger.debug(f"从Redis缓存读取实例 {instance_id} 的账户明细报表")
        return cached_data
    
    instance = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail='Instance not found')
    
    if not instance.vos_uuid:
        raise HTTPException(status_code=400, detail='Instance has no UUID')
    
    vos_uuid = instance.vos_uuid
    
    # 构建查询条件
    query = db.query(AccountDetailReport).filter(
        AccountDetailReport.vos_instance_id == instance_id,
        AccountDetailReport.vos_uuid == vos_uuid
    )
    
    # 如果有账户过滤
    if account:
        query = query.filter(AccountDetailReport.account == account)
    
    # 如果有日期过滤，需要将日期转换为时间戳范围
    # 注意：VOS API返回的时间戳是UTC时间戳（毫秒）
    # 我们需要将查询的日期范围转换为UTC时间戳范围
    if start_date:
        try:
            from datetime import timezone
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            # 将日期转换为当天的0点UTC时间戳（毫秒）
            start_dt_utc = datetime.combine(start_dt, datetime.min.time()).replace(tzinfo=timezone.utc)
            start_timestamp = int(start_dt_utc.timestamp() * 1000)
            query = query.filter(AccountDetailReport.begin_time >= start_timestamp)
        except ValueError:
            raise HTTPException(status_code=400, detail='Invalid start_date format, should be YYYY-MM-DD')
    
    if end_date:
        try:
            from datetime import timezone, timedelta
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            # 将日期转换为当天的23:59:59.999 UTC时间戳（毫秒）
            end_dt_utc = datetime.combine(end_dt, datetime.max.time().replace(microsecond=999000)).replace(tzinfo=timezone.utc)
            end_timestamp = int(end_dt_utc.timestamp() * 1000)
            query = query.filter(AccountDetailReport.end_time <= end_timestamp)
        except ValueError:
            raise HTTPException(status_code=400, detail='Invalid end_date format, should be YYYY-MM-DD')
    
    # 查询数据，按时间倒序
    reports = query.order_by(AccountDetailReport.begin_time.desc()).limit(1000).all()
    
    # 构建响应
    response = {
        'instance_id': instance_id,
        'instance_name': instance.name,
        'reports': [
            {
                'id': report.id,
                'account': report.account,
                'account_name': report.account_name,
                'begin_time': report.begin_time,
                'end_time': report.end_time,
                'begin_datetime': datetime.fromtimestamp(report.begin_time / 1000.0, tz=timezone.utc).isoformat() if report.begin_time else None,
                'end_datetime': datetime.fromtimestamp(report.end_time / 1000.0, tz=timezone.utc).isoformat() if report.end_time else None,
                'report_date': datetime.fromtimestamp(report.begin_time / 1000.0, tz=timezone.utc).date().isoformat() if report.begin_time else None,
                'cdr_count': report.cdr_count,
                'total_fee': float(report.total_fee),
                'total_time': report.total_time,
                'total_suite_fee': float(report.total_suite_fee),
                'total_suite_fee_time': report.total_suite_fee_time,
                'net_fee': float(report.net_fee),
                'net_time': report.net_time,
                'net_count': report.net_count,
                'local_fee': float(report.local_fee),
                'local_time': report.local_time,
                'local_count': report.local_count,
                'domestic_fee': float(report.domestic_fee),
                'domestic_time': report.domestic_time,
                'domestic_count': report.domestic_count,
                'international_fee': float(report.international_fee),
                'international_time': report.international_time,
                'international_count': report.international_count,
                'created_at': report.created_at.isoformat() if report.created_at else None,
                'updated_at': report.updated_at.isoformat() if report.updated_at else None
            }
            for report in reports
        ],
        'total_count': len(reports)
    }
    
    # 写入Redis缓存（5分钟）
    RedisCache.set(cache_key, response, ttl=300)
    
    return response

