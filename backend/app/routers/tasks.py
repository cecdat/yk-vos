"""
任务状态API路由
提供Celery任务队列和同步任务的状态查询
"""
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import logging

from app.core.db import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.tasks.celery_app import celery
from celery.result import AsyncResult

router = APIRouter(prefix='/tasks', tags=['tasks'])
logger = logging.getLogger(__name__)


@router.get('/status')
async def get_task_status(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    获取任务队列状态
    
    返回:
    - active_tasks: 活跃任务数
    - scheduled_tasks: 计划任务数
    - worker_status: Worker状态
    - recent_tasks: 最近任务列表
    """
    try:
        # 获取Celery检查对象
        inspect = celery.control.inspect()
        
        # 获取活跃任务
        active_tasks = inspect.active()
        active_count = 0
        active_list = []
        if active_tasks:
            for worker, tasks in active_tasks.items():
                active_count += len(tasks)
                for task in tasks:
                    active_list.append({
                        'name': task.get('name', '').split('.')[-1],
                        'worker': worker,
                        'id': task.get('id', '')[:8]
                    })
        
        # 获取计划任务（scheduled）
        scheduled_tasks = inspect.scheduled()
        scheduled_count = 0
        if scheduled_tasks:
            for worker, tasks in scheduled_tasks.items():
                scheduled_count += len(tasks)
        
        # 获取保留任务（reserved）
        reserved_tasks = inspect.reserved()
        reserved_count = 0
        if reserved_tasks:
            for worker, tasks in reserved_tasks.items():
                reserved_count += len(tasks)
        
        # 获取Worker状态
        stats = inspect.stats()
        worker_count = len(stats) if stats else 0
        
        # 获取注册的定时任务
        registered_tasks = inspect.registered()
        registered_count = 0
        task_types = set()
        if registered_tasks:
            for worker, tasks in registered_tasks.items():
                registered_count = len(tasks)
                for task in tasks:
                    if 'sync' in task.lower():
                        task_types.add(task.split('.')[-1])
        
        # 构建响应
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'workers': {
                'count': worker_count,
                'status': 'running' if worker_count > 0 else 'stopped'
            },
            'tasks': {
                'active': active_count,
                'scheduled': scheduled_count,
                'reserved': reserved_count,
                'active_list': active_list[:5]  # 最多显示5个
            },
            'sync_tasks': {
                'registered_count': len(task_types),
                'task_types': sorted(list(task_types))
            },
            'status': 'healthy' if worker_count > 0 else 'warning'
        }
        
    except Exception as e:
        logger.exception(f'获取任务状态失败: {e}')
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'workers': {'count': 0, 'status': 'unknown'},
            'tasks': {'active': 0, 'scheduled': 0, 'reserved': 0, 'active_list': []},
            'sync_tasks': {'registered_count': 0, 'task_types': []},
            'status': 'error'
        }


@router.get('/beat-schedule')
async def get_beat_schedule(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    获取Celery Beat定时任务配置
    """
    try:
        from app.tasks.celery_app import celery
        
        schedule = celery.conf.beat_schedule
        
        # 转换为可序列化格式
        formatted_schedule = []
        for name, config in schedule.items():
            task_info = {
                'name': name,
                'task': config.get('task', '').split('.')[-1],
                'schedule': str(config.get('schedule', '')),
                'enabled': True
            }
            formatted_schedule.append(task_info)
        
        return {
            'success': True,
            'schedule_count': len(formatted_schedule),
            'schedules': formatted_schedule
        }
        
    except Exception as e:
        logger.exception(f'获取定时任务配置失败: {e}')
        return {
            'success': False,
            'error': str(e),
            'schedule_count': 0,
            'schedules': []
        }


@router.get('/recent-logs')
async def get_recent_task_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 10
):
    """
    获取最近的任务日志（从Celery结果后端）
    注意：需要配置result_backend才能使用
    """
    # TODO: 实现从Redis或数据库读取任务结果历史
    # 当前返回示例数据
    return {
        'success': True,
        'message': '任务日志功能需要配置Celery result_backend',
        'logs': []
    }


@router.get('/cdr-sync-status')
async def get_cdr_sync_status(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    获取历史话单同步状态（带Redis缓存）
    
    返回:
    - 最后同步时间
    - 同步的数据量
    - 任务状态（运行中/成功/失败）
    """
    from app.core.redis_cache import RedisCache
    
    # Redis缓存键（缓存30秒，因为状态变化较快）
    cache_key = 'cdr_sync_status'
    cached_data = RedisCache.get(cache_key)
    if cached_data is not None:
        logger.debug("从Redis缓存读取CDR同步状态")
        return cached_data
    
    try:
        from app.models.clickhouse_cdr import ClickHouseCDR
        from app.models.vos_instance import VOSInstance
        
        # 获取所有启用的VOS实例
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        
):
    """
    获取所有同步任务的进度（统一接口）
    
    返回当前正在进行的同步任务信息，包括：
    - CDR同步（历史话单）
    - 客户数据同步
    - 网关同步
    - 账户明细报表同步
    """
    try:
        from app.core.config import settings
        import redis
        import json
        from celery.result import AsyncResult
        
        # 连接 Redis
        r = redis.from_url(settings.REDIS_URL)
        
        # 获取所有类型的同步任务进度
        sync_tasks = []
        
        # 1. CDR同步进度
        cdr_progress_data = r.get('cdr_sync_progress')
        if cdr_progress_data:
            try:
                cdr_progress = json.loads(cdr_progress_data)
                status = cdr_progress.get('status', 'unknown')
                if status != 'completed':
                    # 计算进度百分比
                    progress_percent = 0
                    if status == 'task_created':
                        progress_percent = 0
                    elif status == 'syncing':
                        total_tasks = cdr_progress.get('total_tasks')
                        completed_tasks = cdr_progress.get('completed_tasks', 0)
                        if total_tasks and total_tasks > 0:
                            current_task_progress = 0
                            if cdr_progress.get('current_customer_index') and cdr_progress.get('total_customers'):
                                current_task_progress = (cdr_progress.get('current_customer_index', 0) / cdr_progress.get('total_customers', 1)) * (1 / total_tasks)
                            progress_percent = round((completed_tasks / total_tasks) * 100 + current_task_progress * 100, 1)
                            progress_percent = min(progress_percent, 100)
                        else:
                            if cdr_progress.get('current_customer_index') and cdr_progress.get('total_customers'):
                                progress_percent = round((cdr_progress.get('current_customer_index', 0) / cdr_progress.get('total_customers', 1)) * 100, 1)
                    
                    sync_tasks.append({
                        'task_type': 'cdr',
                        'task_name': '历史话单同步',
                        'status': status,
                        'progress_percent': progress_percent,
                        'current_instance': cdr_progress.get('current_instance'),
                        'current_customer': cdr_progress.get('current_customer'),
                        'current_customer_index': cdr_progress.get('current_customer_index'),
                        'total_customers': cdr_progress.get('total_customers'),
                        'total_tasks': cdr_progress.get('total_tasks'),
                        'completed_tasks': cdr_progress.get('completed_tasks', 0),
                        'synced_count': cdr_progress.get('synced_count', 0),
                        'sync_date': cdr_progress.get('sync_date'),
                        'days': cdr_progress.get('days'),
                        'instances_count': cdr_progress.get('instances_count'),
                        'start_time': cdr_progress.get('start_time'),
                        'message': cdr_progress.get('message', '正在同步历史话单...')
                    })
            except Exception as e:
                logger.error(f'解析CDR同步进度失败: {e}')
        
        # 2. 客户数据同步进度
        customer_progress_data = r.get('customer_sync_progress')
        if customer_progress_data:
            try:
                customer_progress = json.loads(customer_progress_data)
                status = customer_progress.get('status', 'unknown')
                if status != 'completed':
                    progress_percent = customer_progress.get('progress_percent', 0)
                    sync_tasks.append({
                        'task_type': 'customer',
                        'task_name': '客户数据同步',
                        'status': status,
                        'progress_percent': progress_percent,
                        'current_instance': customer_progress.get('current_instance'),
                        'current_instance_id': customer_progress.get('current_instance_id'),
                        'total_instances': customer_progress.get('total_instances'),
                        'completed_instances': customer_progress.get('completed_instances', 0),
                        'synced_count': customer_progress.get('synced_count', 0),
                        'start_time': customer_progress.get('start_time'),
                        'message': customer_progress.get('message', '正在同步客户数据...')
                    })
            except Exception as e:
                logger.error(f'解析客户数据同步进度失败: {e}')
        
        # 3. 网关同步进度
        gateway_progress_data = r.get('gateway_sync_progress')
        if gateway_progress_data:
            try:
                gateway_progress = json.loads(gateway_progress_data)
                status = gateway_progress.get('status', 'unknown')
                if status != 'completed':
                    progress_percent = gateway_progress.get('progress_percent', 0)
                    sync_tasks.append({
                        'task_type': 'gateway',
                        'task_name': '网关数据同步',
                        'status': status,
                        'progress_percent': progress_percent,
                        'current_instance': gateway_progress.get('current_instance'),
                        'current_instance_id': gateway_progress.get('current_instance_id'),
                        'total_instances': gateway_progress.get('total_instances'),
                        'completed_instances': gateway_progress.get('completed_instances', 0),
                        'synced_count': gateway_progress.get('synced_count', 0),
                        'start_time': gateway_progress.get('start_time'),
                        'message': gateway_progress.get('message', '正在同步网关数据...')
                    })
            except Exception as e:
                logger.error(f'解析网关同步进度失败: {e}')
        
        # 4. 账户明细报表同步进度
        account_report_progress_data = r.get('account_detail_report_sync_progress')
        if account_report_progress_data:
            try:
                account_report_progress = json.loads(account_report_progress_data)
                status = account_report_progress.get('status', 'unknown')
                if status != 'completed':
                    progress_percent = account_report_progress.get('progress_percent', 0)
                    sync_tasks.append({
                        'task_type': 'account_detail_report',
                        'task_name': '账户明细报表同步',
                        'status': status,
                        'progress_percent': progress_percent,
                        'current_instance': account_report_progress.get('current_instance'),
                        'current_instance_id': account_report_progress.get('current_instance_id'),
                        'current_account': account_report_progress.get('current_account'),
                        'sync_date': account_report_progress.get('sync_date'),
                        'total_tasks': account_report_progress.get('total_tasks'),
                        'completed_tasks': account_report_progress.get('completed_tasks', 0),
                        'synced_count': account_report_progress.get('synced_count', 0),
                        'start_time': account_report_progress.get('start_time'),
                        'message': account_report_progress.get('message', '正在同步账户明细报表...')
                    })
            except Exception as e:
                logger.error(f'解析账户明细报表同步进度失败: {e}')
        
        return {
            'success': True,
            'has_active_tasks': len(sync_tasks) > 0,
            'tasks': sync_tasks,
            'tasks_count': len(sync_tasks)
        }
        
    except Exception as e:
        logger.exception(f'获取同步任务进度失败: {e}')
        return {
            'success': False,
            'error': str(e),
            'has_active_tasks': False,
            'tasks': []
        }