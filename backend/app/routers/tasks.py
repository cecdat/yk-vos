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
        
        if not instances:
            return {
                'success': True,
                'status': 'no_instances',
                'message': '没有启用的VOS实例',
                'instances': []
            }
        
        # 获取每个实例的同步状态
        instance_stats = []
        total_count = 0
        latest_sync_time = None
        
        for inst in instances:
            try:
                # 查询最近的话单数据（获取最后同步时间和数量）
                count, last_sync = ClickHouseCDR.get_sync_status(vos_id=inst.id)
                total_count += count
                
                if last_sync and (not latest_sync_time or last_sync > latest_sync_time):
                    latest_sync_time = last_sync
                
                # 转换UTC时间到东八区（Asia/Shanghai）
                last_sync_str = None
                if last_sync:
                    # ClickHouse返回的是naive datetime（UTC），需要添加时区信息
                    utc_time = last_sync.replace(tzinfo=timezone.utc)
                    # 转换为东八区时间
                    cn_time = utc_time.astimezone(timezone(timedelta(hours=8)))
                    last_sync_str = cn_time.isoformat()
                
                instance_stats.append({
                    'instance_id': inst.id,
                    'instance_name': inst.name,
                    'total_cdrs': count,
                    'last_sync_time': last_sync_str,
                    'status': 'synced' if count > 0 else 'empty'
                })
            except Exception as e:
                logger.error(f'获取VOS实例 {inst.name} 同步状态失败: {e}')
                instance_stats.append({
                    'instance_id': inst.id,
                    'instance_name': inst.name,
                    'total_cdrs': 0,
                    'last_sync_time': None,
                    'status': 'error',
                    'error': str(e)
                })
        
        # 检查任务是否正在运行
        inspect = celery.control.inspect()
        active_tasks = inspect.active()
        is_syncing = False
        
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    if 'sync_all_instances_cdrs' in task.get('name', '') or 'sync_cdrs_for_single_day' in task.get('name', ''):
                        is_syncing = True
                        break
        
        # 转换最后同步时间到东八区
        latest_sync_str = None
        if latest_sync_time:
            utc_time = latest_sync_time.replace(tzinfo=timezone.utc)
            cn_time = utc_time.astimezone(timezone(timedelta(hours=8)))
            latest_sync_str = cn_time.isoformat()
        
        response = {
            'success': True,
            'status': 'syncing' if is_syncing else 'idle',
            'is_syncing': is_syncing,
            'total_cdrs': total_count,
            'last_sync_time': latest_sync_str,
            'instances_count': len(instances),
            'instances': instance_stats,
            'next_sync': '每天凌晨 01:30 自动同步'
        }
        
        # 写入Redis缓存（30秒，因为同步状态变化较快）
        RedisCache.set(cache_key, response, ttl=30)
        
        return response
        
    except Exception as e:
        logger.exception(f'获取话单同步状态失败: {e}')
        return {
            'success': False,
            'error': str(e),
            'status': 'error',
            'total_cdrs': 0,
            'last_sync_time': None,
            'instances': []
        }


@router.get('/cdr-sync-progress')
async def get_cdr_sync_progress(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    获取当前话单同步进度（实时）
    
    从 Redis 获取正在进行的同步任务的详细进度
    """
    try:
        from app.core.config import settings
        import redis
        import json
        
        # 连接 Redis
        r = redis.from_url(settings.REDIS_URL)
        
        # 获取同步进度
        progress_data = r.get('cdr_sync_progress')
        
        if not progress_data:
            return {
                'success': True,
                'is_syncing': False,
                'message': '当前没有正在进行的同步任务'
            }
        
        # 解析进度数据
        progress = json.loads(progress_data)
        
        return {
            'success': True,
            'is_syncing': True,
            'status': progress.get('status', 'unknown'),
            'current_instance': progress.get('current_instance'),
            'current_instance_id': progress.get('current_instance_id'),
            'current_customer': progress.get('current_customer'),
            'current_customer_index': progress.get('current_customer_index'),
            'total_customers': progress.get('total_customers'),
            'synced_count': progress.get('synced_count', 0),
            'start_time': progress.get('start_time'),
            'progress_percent': round((progress.get('current_customer_index', 0) / progress.get('total_customers', 1)) * 100, 1) if progress.get('total_customers') else 0
        }
        
    except Exception as e:
        logger.exception(f'获取同步进度失败: {e}')
        return {
            'success': False,
            'error': str(e),
            'is_syncing': False
        }