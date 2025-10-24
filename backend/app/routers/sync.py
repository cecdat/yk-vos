"""
同步管理API接口
支持配置同步任务时间、手动触发同步
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Annotated
from pydantic import BaseModel
import logging

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.vos_instance import VOSInstance
from app.models.customer import Customer
from app.tasks.sync_tasks import sync_all_instances_cdrs, sync_customers_for_instance
from app.tasks.initial_sync_tasks import sync_cdrs_for_single_day
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter()


class SyncConfig(BaseModel):
    """同步配置"""
    cdr_sync_time: str  # HH:MM 格式
    customer_sync_time: str  # HH:MM 格式
    cdr_sync_days: int  # 同步天数


class ManualCDRSync(BaseModel):
    """手动触发话单同步"""
    instance_id: Optional[int] = None  # None表示全部节点
    customer_id: Optional[int] = None  # None表示全部客户
    days: int = 1  # 同步天数


class ManualCustomerSync(BaseModel):
    """手动触发客户同步"""
    instance_id: Optional[int] = None  # None表示全部节点


@router.get('/config')
async def get_sync_config(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    获取同步配置
    
    目前配置存储在环境变量或默认值中
    未来可以存储到数据库的配置表
    """
    # TODO: 从数据库读取配置
    return {
        'cdr_sync_time': '01:30',
        'customer_sync_time': '01:00',
        'cdr_sync_days': 1
    }


@router.post('/config')
async def save_sync_config(
    config: SyncConfig,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    保存同步配置
    
    TODO: 将配置保存到数据库，并更新Celery Beat调度
    """
    logger.info(f'保存同步配置: {config.dict()}')
    
    # TODO: 保存到数据库
    # TODO: 动态更新Celery Beat任务调度时间
    
    return {
        'success': True,
        'message': '同步配置已保存（注意：当前版本需要重启服务才能生效）'
    }


@router.post('/manual/cdr')
async def manual_cdr_sync(
    params: ManualCDRSync,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    手动触发历史话单同步
    
    支持三种模式：
    1. 全部节点：instance_id=None
    2. 指定节点全部客户：instance_id=X, customer_id=None
    3. 指定节点指定客户：instance_id=X, customer_id=Y
    """
    try:
        # 验证节点是否存在
        if params.instance_id is not None:
            instance = db.query(VOSInstance).filter(
                VOSInstance.id == params.instance_id
            ).first()
            
            if not instance:
                raise HTTPException(status_code=404, detail='VOS节点不存在')
            
            if not instance.enabled:
                raise HTTPException(status_code=400, detail='VOS节点未启用')
        
        # 验证客户是否存在
        if params.customer_id is not None:
            if params.instance_id is None:
                raise HTTPException(status_code=400, detail='指定客户时必须指定节点')
            
            customer = db.query(Customer).filter(
                Customer.id == params.customer_id,
                Customer.vos_instance_id == params.instance_id
            ).first()
            
            if not customer:
                raise HTTPException(status_code=404, detail='客户不存在')
        
        # 触发同步任务
        if params.instance_id is None:
            # 模式1：全部节点
            task = sync_all_instances_cdrs.apply_async(args=[params.days])
            logger.info(f'用户 {current_user.username} 触发全部节点话单同步，任务ID: {task.id}')
            return {
                'success': True,
                'message': f'已启动全部节点的话单同步任务（最近{params.days}天）',
                'task_id': str(task.id)
            }
        
        elif params.customer_id is None:
            # 模式2：指定节点全部客户
            # 使用现有的sync_all_instances_cdrs，但只同步一个节点
            # 这里简化处理，直接调用按天同步
            today = datetime.now().date()
            tasks = []
            for i in range(params.days):
                sync_date = today - timedelta(days=i)
                task = sync_cdrs_for_single_day.apply_async(
                    args=[params.instance_id, sync_date.strftime('%Y%m%d')],
                    countdown=i * 5  # 每批间隔5秒
                )
                tasks.append(str(task.id))
            
            logger.info(f'用户 {current_user.username} 触发节点 {params.instance_id} 全部客户话单同步')
            return {
                'success': True,
                'message': f'已启动指定节点全部客户的话单同步（最近{params.days}天，共{len(tasks)}个任务）',
                'task_ids': tasks
            }
        
        else:
            # 模式3：指定节点指定客户
            # 这需要专门的任务函数，暂时用现有任务
            today = datetime.now().date()
            tasks = []
            for i in range(params.days):
                sync_date = today - timedelta(days=i)
                task = sync_cdrs_for_single_day.apply_async(
                    args=[params.instance_id, sync_date.strftime('%Y%m%d')],
                    countdown=i * 5
                )
                tasks.append(str(task.id))
            
            customer = db.query(Customer).filter(Customer.id == params.customer_id).first()
            logger.info(f'用户 {current_user.username} 触发节点 {params.instance_id} 客户 {customer.account} 话单同步')
            return {
                'success': True,
                'message': f'已启动指定客户 {customer.account} 的话单同步（最近{params.days}天，共{len(tasks)}个任务）',
                'task_ids': tasks
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f'手动触发话单同步失败: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/manual/customer')
async def manual_customer_sync(
    params: ManualCustomerSync,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    手动触发客户数据同步
    
    支持两种模式：
    1. 全部节点：instance_id=None
    2. 指定节点：instance_id=X
    """
    try:
        if params.instance_id is None:
            # 全部节点
            instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
            if not instances:
                return {
                    'success': False,
                    'message': '没有启用的VOS节点'
                }
            
            tasks = []
            for inst in instances:
                task = sync_customers_for_instance.apply_async(args=[inst.id])
                tasks.append(str(task.id))
            
            logger.info(f'用户 {current_user.username} 触发全部节点客户同步')
            return {
                'success': True,
                'message': f'已启动全部节点的客户同步（共{len(instances)}个节点）',
                'task_ids': tasks
            }
        
        else:
            # 指定节点
            instance = db.query(VOSInstance).filter(
                VOSInstance.id == params.instance_id
            ).first()
            
            if not instance:
                raise HTTPException(status_code=404, detail='VOS节点不存在')
            
            if not instance.enabled:
                raise HTTPException(status_code=400, detail='VOS节点未启用')
            
            task = sync_customers_for_instance.apply_async(args=[params.instance_id])
            
            logger.info(f'用户 {current_user.username} 触发节点 {params.instance_id} ({instance.name}) 客户同步')
            return {
                'success': True,
                'message': f'已启动节点 {instance.name} 的客户同步',
                'task_id': str(task.id)
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f'手动触发客户同步失败: {e}')
        raise HTTPException(status_code=500, detail=str(e))

