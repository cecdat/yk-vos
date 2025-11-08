"""
同步管理API接口
支持配置同步任务时间、手动触发同步
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Annotated
from pydantic import BaseModel
import logging

from app.core.db import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.vos_instance import VOSInstance
from app.models.customer import Customer
from app.models.app_config import AppConfig
from app.tasks.sync_tasks import sync_all_instances_cdrs, sync_customers_for_instance, sync_instance_gateways_enhanced, sync_all_instances_gateways
from app.tasks.initial_sync_tasks import sync_cdrs_for_single_day
from app.tasks.manual_sync_tasks import sync_single_customer_cdrs
from app.tasks.account_detail_report_tasks import sync_account_detail_reports_daily, sync_single_instance_account_detail_reports
from datetime import datetime, timedelta, date

logger = logging.getLogger(__name__)
router = APIRouter()


class SyncConfig(BaseModel):
    """同步配置"""
    cdr_sync_time: str  # HH:MM 格式
    customer_sync_time: str  # HH:MM 格式
    cdr_sync_days: int  # 同步天数
    gateway_sync_time: Optional[str] = None  # HH:MM 格式
    account_detail_report_sync_time: Optional[str] = None  # HH:MM 格式
    account_detail_report_sync_days: Optional[int] = 1  # 账户明细报表同步天数


class ManualCDRSync(BaseModel):
    """手动触发话单同步"""
    instance_id: Optional[int] = None  # None表示全部节点
    customer_id: Optional[int] = None  # None表示全部客户
    days: int = 1  # 同步天数


class ManualCustomerSync(BaseModel):
    """手动触发客户同步"""
    instance_id: Optional[int] = None  # None表示全部节点


class ManualGatewaySync(BaseModel):
    """手动触发网关同步"""
    instance_id: Optional[int] = None  # None表示全部节点
    gateway_type: str = 'both'  # 'mapping', 'routing', 'both'


@router.get('/config')
async def get_sync_config(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    获取同步配置
    
    从数据库读取配置，如果不存在则返回默认值
    """
    def get_config_value(key: str, default: str) -> str:
        """从数据库获取配置值，如果不存在则返回默认值"""
        config = db.query(AppConfig).filter(AppConfig.config_key == key).first()
        return config.config_value if config else default
    
    def get_config_int(key: str, default: int) -> int:
        """从数据库获取配置值（整数），如果不存在则返回默认值"""
        config = db.query(AppConfig).filter(AppConfig.config_key == key).first()
        if config and config.config_value:
            try:
                return int(config.config_value)
            except ValueError:
                return default
        return default
    
    return {
        'cdr_sync_time': get_config_value('cdr_sync_time', '01:30'),
        'customer_sync_time': get_config_value('customer_sync_time', '01:00'),
        'cdr_sync_days': get_config_int('cdr_sync_days', 1),
        'gateway_sync_time': get_config_value('gateway_sync_time', '02:00'),
        'account_detail_report_sync_time': get_config_value('account_detail_report_sync_time', '03:00'),
        'account_detail_report_sync_days': get_config_int('account_detail_report_sync_days', 1)
    }


@router.post('/config')
async def save_sync_config(
    config: SyncConfig,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    保存同步配置
    
    将配置保存到数据库
    TODO: 动态更新Celery Beat任务调度时间
    """
    logger.info(f'保存同步配置: {config.dict()}')
    
    def save_config(key: str, value: str, description: str = ''):
        """保存或更新配置项"""
        app_config = db.query(AppConfig).filter(AppConfig.config_key == key).first()
        if app_config:
            app_config.config_value = value
            if description:
                app_config.description = description
        else:
            app_config = AppConfig(
                config_key=key,
                config_value=value,
                description=description
            )
            db.add(app_config)
    
    # 保存配置
    save_config('cdr_sync_time', config.cdr_sync_time, 'CDR同步时间（HH:MM格式）')
    save_config('customer_sync_time', config.customer_sync_time, '客户数据同步时间（HH:MM格式）')
    save_config('cdr_sync_days', str(config.cdr_sync_days), 'CDR同步天数（1-30天）')
    
    if config.gateway_sync_time:
        save_config('gateway_sync_time', config.gateway_sync_time, '网关数据同步时间（HH:MM格式）')
    if config.account_detail_report_sync_time:
        save_config('account_detail_report_sync_time', config.account_detail_report_sync_time, '账户明细报表同步时间（HH:MM格式）')
    if config.account_detail_report_sync_days is not None:
        save_config('account_detail_report_sync_days', str(config.account_detail_report_sync_days), '账户明细报表同步天数（1-30天）')
    
    db.commit()
    
    logger.info(f'同步配置已保存到数据库')
    
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
            # 注意：sync_all_instances_cdrs 现在会创建多个任务（按天、按实例）
            task = sync_all_instances_cdrs.apply_async(args=[params.days])
            logger.info(f'用户 {current_user.username} 触发全部节点话单同步，将创建多个任务（每个实例×{params.days}天）')
            return {
                'success': True,
                'message': f'已启动全部节点的话单同步（最近{params.days}天），系统将按天创建多个任务以避免VOS卡死',
                'task_id': str(task.id),
                'note': '此任务会创建多个子任务，每个实例每天一个任务，任务将按计划延迟执行'
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
            customer = db.query(Customer).filter(Customer.id == params.customer_id).first()
            
            # 使用专门的单客户同步任务
            # 注意：如果 days > 1，会创建多个任务（每天一个）
            task = sync_single_customer_cdrs.apply_async(
                args=[params.instance_id, params.customer_id, params.days]
            )
            
            logger.info(f'用户 {current_user.username} 触发节点 {params.instance_id} 客户 {customer.account} 话单同步（{params.days}天）')
            message = f'已启动客户 {customer.account} 的话单同步'
            if params.days > 1:
                message += f'（最近{params.days}天），系统将按天创建多个任务以避免VOS卡死'
            else:
                message += f'（最近{params.days}天）'
            
            return {
                'success': True,
                'message': message,
                'task_id': str(task.id),
                'customer': customer.account,
                'days': params.days,
                'note': f'多天同步时会创建{params.days}个任务，任务将按计划延迟执行' if params.days > 1 else None
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


@router.post('/manual/gateway')
async def manual_gateway_sync(
    params: ManualGatewaySync,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    手动触发网关同步
    
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
            
            task = sync_all_instances_gateways.apply_async()
            
            logger.info(f'用户 {current_user.username} 触发全部节点网关同步')
            return {
                'success': True,
                'message': f'已启动全部节点的网关同步（共{len(instances)}个节点）',
                'task_id': str(task.id)
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
            
            task = sync_instance_gateways_enhanced.apply_async(args=[params.instance_id])
            
            logger.info(f'用户 {current_user.username} 触发节点 {params.instance_id} ({instance.name}) 网关同步')
            return {
                'success': True,
                'message': f'已启动节点 {instance.name} 的网关同步',
                'task_id': str(task.id)
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f'手动触发网关同步失败: {e}')
        raise HTTPException(status_code=500, detail=str(e))


class ManualAccountDetailReportSync(BaseModel):
    """手动触发账户明细报表同步"""
    instance_id: Optional[int] = None  # None表示全部节点
    days: int = 1  # 同步天数（默认1天，即昨天）


@router.post('/manual/account-detail-report')
async def manual_account_detail_report_sync(
    params: ManualAccountDetailReportSync,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    手动触发账户明细报表同步
    
    支持两种模式：
    1. 全部节点：instance_id=None
    2. 指定节点：instance_id=X
    
    支持多天同步：days参数指定同步最近N天的数据（类似历史话单同步）
    """
    try:
        # 验证同步天数
        if params.days < 1 or params.days > 30:
            raise HTTPException(status_code=400, detail='同步天数必须在1-30天之间')
        
        # 验证节点是否存在
        if params.instance_id is not None:
            instance = db.query(VOSInstance).filter(
                VOSInstance.id == params.instance_id
            ).first()
            
            if not instance:
                raise HTTPException(status_code=404, detail='VOS节点不存在')
            
            if not instance.enabled:
                raise HTTPException(status_code=400, detail='VOS节点未启用')
        
        # 计算需要同步的日期列表
        today = date.today()
        sync_dates = [today - timedelta(days=i) for i in range(params.days)]
        
        if params.instance_id is None:
            # 全部节点
            instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
            if not instances:
                return {
                    'success': False,
                    'message': '没有启用的VOS节点'
                }
            
            # 为每个实例和每天创建任务
            tasks = []
            task_count = 0
            for inst in instances:
                for i, sync_date in enumerate(sync_dates):
                    # 延迟执行，避免对VOS服务器造成压力
                    countdown = task_count * 5  # 每5秒创建一个任务
                    task = sync_single_instance_account_detail_reports.apply_async(
                        args=[inst.id, sync_date],
                        countdown=countdown
                    )
                    tasks.append(str(task.id))
                    task_count += 1
            
            logger.info(f'用户 {current_user.username} 触发全部节点账户明细报表同步，{params.days}天，共{len(instances)}个节点，将创建{len(tasks)}个任务')
            return {
                'success': True,
                'message': f'已启动全部节点的账户明细报表同步（最近{params.days}天，共{len(instances)}个节点），系统将创建{len(tasks)}个任务按计划延迟执行',
                'task_ids': tasks,
                'days': params.days,
                'instances_count': len(instances),
                'tasks_count': len(tasks),
                'note': '此任务会创建多个子任务，每个实例每天一个任务，任务将按计划延迟执行以避免VOS卡死'
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
            
            if params.days == 1:
                # 单天同步，直接执行
                sync_date = today - timedelta(days=1)
                task = sync_single_instance_account_detail_reports.apply_async(
                    args=[params.instance_id, sync_date]
                )
                
                logger.info(f'用户 {current_user.username} 触发节点 {params.instance_id} ({instance.name}) 账户明细报表同步，日期: {sync_date}')
                return {
                    'success': True,
                    'message': f'已启动节点 {instance.name} 的账户明细报表同步（日期: {sync_date}）',
                    'task_id': str(task.id),
                    'target_date': sync_date.isoformat()
                }
            else:
                # 多天同步，创建多个任务
                tasks = []
                for i, sync_date in enumerate(sync_dates):
                    # 延迟执行，避免对VOS服务器造成压力
                    countdown = i * 5  # 每5秒创建一个任务
                    task = sync_single_instance_account_detail_reports.apply_async(
                        args=[params.instance_id, sync_date],
                        countdown=countdown
                    )
                    tasks.append(str(task.id))
                
                logger.info(f'用户 {current_user.username} 触发节点 {params.instance_id} ({instance.name}) 账户明细报表同步，{params.days}天，将创建{len(tasks)}个任务')
                return {
                    'success': True,
                    'message': f'已启动节点 {instance.name} 的账户明细报表同步（最近{params.days}天），系统将创建{len(tasks)}个任务按计划延迟执行',
                    'task_ids': tasks,
                    'days': params.days,
                    'tasks_count': len(tasks),
                    'note': f'多天同步时会创建{params.days}个任务，任务将按计划延迟执行以避免VOS卡死'
                }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f'手动触发账户明细报表同步失败: {e}')
        raise HTTPException(status_code=500, detail=str(e))

