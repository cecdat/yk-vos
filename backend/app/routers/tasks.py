"""
任务状态API路由
提供Celery任务队列和同步任务的状态查询
"""
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
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

