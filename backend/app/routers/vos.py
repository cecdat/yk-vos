from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import logging

from app.core.db import get_db
from app.core.vos_client import VOSClient
from app.models.user import User
from app.models.vos_instance import VOSInstance
from app.models.phone import Phone
from app.models.customer import Customer
from app.models.vos_health import VOSHealthCheck
from app.routers.auth import get_current_user
from app.tasks.sync_tasks import sync_customers_for_instance, check_vos_instances_health
from app.tasks.initial_sync_tasks import initial_sync_for_new_instance

router = APIRouter(prefix='/vos', tags=['vos'])
logger = logging.getLogger(__name__)

# Pydantic schemas for VOS instance
class VOSInstanceCreate(BaseModel):
    name: str
    base_url: str
    description: Optional[str] = None
    enabled: bool = True

class VOSInstanceUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None

@router.get('/instances')
async def get_instances(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
    result = []
    
    for inst in instances:
        # 获取健康检查状态
        health_check = db.query(VOSHealthCheck).filter(
            VOSHealthCheck.vos_instance_id == inst.id
        ).first()
        
        instance_data = {
            'id': inst.id,
            'name': inst.name,
            'base_url': inst.base_url,
            'description': inst.description,
            'enabled': inst.enabled,
            'health_status': health_check.status if health_check else 'unknown',
            'health_last_check': health_check.last_check_at.isoformat() if health_check and health_check.last_check_at else None,
            'health_response_time': health_check.response_time_ms if health_check else None,
            'health_error': health_check.error_message if health_check else None
        }
        result.append(instance_data)
    
    return result

@router.get('/instances/{instance_id}')
async def get_instance(
    instance_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    instance = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail='Instance not found')
    return {
        'id': instance.id,
        'name': instance.name,
        'base_url': instance.base_url,
        'description': instance.description,
        'enabled': instance.enabled
    }

@router.get('/instances/{instance_id}/phones/online')
async def get_instance_online_phones(
    instance_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    instance = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail='Instance not found')
    
    # 调用 VOS API 获取在线话机
    client = VOSClient(instance.base_url)
    res = client.post('/external/server/GetPhoneOnline', payload={})
    
    # 检查 API 调用是否成功
    if not client.is_success(res):
        error_msg = client.get_error_message(res)
        raise HTTPException(
            status_code=500,
            detail=f'Failed to get online phones from VOS: {error_msg}'
        )
    
    # 尝试不同的响应格式
    phones = res.get('infoPhoneOnlines') or res.get('phones') or []
    if not isinstance(phones, list):
        for v in res.values():
            if isinstance(v, list):
                phones = v
                break
    
    return {'infoPhoneOnlines': phones, 'count': len(phones)}

@router.get('/instances/{instance_id}/phones')
async def get_instance_phones(
    instance_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    phones = db.query(Phone).filter(Phone.vos_id == instance_id).all()
    return [
        {
            'id': phone.id,
            'e164': phone.e164,
            'status': phone.status,
            'last_seen': phone.last_seen.isoformat() if phone.last_seen else None,
            'vos_id': phone.vos_id
        }
        for phone in phones
    ]

@router.post('/instances')
async def create_instance(
    instance_data: VOSInstanceCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    # 检查是否已存在相同名称的实例
    existing = db.query(VOSInstance).filter(VOSInstance.name == instance_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail='Instance with this name already exists')
    
    new_instance = VOSInstance(
        name=instance_data.name,
        base_url=instance_data.base_url.rstrip('/'),
        description=instance_data.description,
        enabled=instance_data.enabled
    )
    db.add(new_instance)
    db.commit()
    db.refresh(new_instance)
    
    # 触发初始化同步任务（异步）
    # 1. 同步客户数据
    # 2. 分批同步最近一周的历史话单
    if new_instance.enabled:
        logger.info(f'🚀 触发新VOS节点 {new_instance.name} 的初始化同步任务')
        initial_sync_for_new_instance.delay(new_instance.id)
    
    return {
        'id': new_instance.id,
        'name': new_instance.name,
        'base_url': new_instance.base_url,
        'description': new_instance.description,
        'enabled': new_instance.enabled,
        'message': 'VOS节点创建成功，正在后台初始化数据同步（客户数据 + 最近7天话单）...'
    }

@router.put('/instances/{instance_id}')
async def update_instance(
    instance_id: int,
    instance_data: VOSInstanceUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    instance = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail='Instance not found')
    
    # 更新字段
    if instance_data.name is not None:
        instance.name = instance_data.name
    if instance_data.base_url is not None:
        instance.base_url = instance_data.base_url.rstrip('/')
    if instance_data.description is not None:
        instance.description = instance_data.description
    if instance_data.enabled is not None:
        instance.enabled = instance_data.enabled
    
    db.commit()
    db.refresh(instance)
    
    return {
        'id': instance.id,
        'name': instance.name,
        'base_url': instance.base_url,
        'description': instance.description,
        'enabled': instance.enabled,
        'message': 'Instance updated successfully'
    }

@router.delete('/instances/{instance_id}')
async def delete_instance(
    instance_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    instance = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail='Instance not found')
    
    logger.info(f'正在删除 VOS 实例: {instance.name} (ID={instance_id})')
    
    try:
        # 删除相关的 customers
        customer_count = db.query(Customer).filter(Customer.vos_instance_id == instance_id).delete()
        logger.info(f'删除了 {customer_count} 个客户记录')
        
        # 删除相关的 phones
        phone_count = db.query(Phone).filter(Phone.vos_id == instance_id).delete()
        logger.info(f'删除了 {phone_count} 个话机记录')
        
        # 删除相关的缓存数据（如果有）
        from app.models.vos_data_cache import VosDataCache
        cache_count = db.query(VosDataCache).filter(VosDataCache.vos_instance_id == instance_id).delete()
        logger.info(f'删除了 {cache_count} 个缓存记录')
        
        # 删除相关的 CDR 数据（可选，如果数据量大可能很慢）
        from app.models.cdr import CDR
        cdr_count = db.query(CDR).filter(CDR.vos_id == instance_id).delete()
        logger.info(f'删除了 {cdr_count} 个话单记录')
        
        # 最后删除实例本身
        db.delete(instance)
        db.commit()
        
        logger.info(f'成功删除 VOS 实例: {instance.name}')
        
        return {
            'message': 'VOS 实例删除成功',
            'deleted': {
                'instance_name': instance.name,
                'customers': customer_count,
                'phones': phone_count,
                'cache_entries': cache_count,
                'cdrs': cdr_count
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f'删除 VOS 实例失败: {e}')
        raise HTTPException(status_code=500, detail=f'删除失败: {str(e)}')

@router.get('/customers/{instance_id}')
async def get_customers_by_instance(
    instance_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    获取指定 VOS 实例的所有客户（简化版，用于下拉选择）
    从数据库直接读取
    """
    instance = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail='VOS实例未找到')
    
    customers = db.query(Customer).filter(
        Customer.vos_instance_id == instance_id
    ).all()
    
    return [
        {
            'id': c.id,
            'account': c.account,
            'vos_instance_id': c.vos_instance_id
        }
        for c in customers
    ]


@router.get('/instances/{instance_id}/customers')
async def get_instance_customers(
    instance_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False, description="强制从VOS刷新数据")
):
    """
    获取指定 VOS 实例的所有客户（详细版）
    三级缓存策略：Redis → PostgreSQL → VOS API
    """
    instance = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail='VOS实例未找到')
    
    # 如果强制刷新，清除缓存并触发同步
    if refresh:
        logger.info(f'强制刷新VOS {instance.name} 客户数据')
        sync_customers_for_instance.delay(instance_id)
        # 立即从VOS查询最新数据
        client = VOSClient(instance.base_url)
        try:
            result = client.call_api('/external/server/GetAllCustomers', {'type': 1})
            if client.is_success(result):
                customers = result.get('infoCustomerBriefs', [])
                logger.info(f'从VOS {instance.name} 获取到 {len(customers)} 个客户')
                return {
                    'customers': customers,
                    'count': len(customers),
                    'instance_id': instance_id,
                    'instance_name': instance.name,
                    'from_cache': False,
                    'data_source': 'vos_api',
                    'message': '数据已从VOS刷新，后台同步进行中'
                }
        except Exception as e:
            logger.error(f'从VOS {instance.name} 刷新客户数据失败: {e}')
            pass  # 失败则继续从数据库读取
    
    # 1️⃣ 先从本地数据库读取
    customers_db = db.query(Customer).filter(
        Customer.vos_instance_id == instance_id
    ).order_by(Customer.account).all()
    
    # 2️⃣ 如果数据库中有数据，直接返回
    if customers_db:
        logger.info(f'从本地数据库读取到 {len(customers_db)} 个客户 (VOS: {instance.name})')
        customers = [
            {
                'account': c.account,
                'money': c.money,
                'limitMoney': c.limit_money,
                'is_in_debt': c.is_in_debt
            }
            for c in customers_db
        ]
        
        latest_sync = customers_db[0].synced_at if customers_db else None
        
        return {
            'customers': customers,
            'count': len(customers),
            'instance_id': instance_id,
            'instance_name': instance.name,
            'from_cache': True,
            'data_source': 'database',
            'last_synced_at': latest_sync.isoformat() if latest_sync else None
        }
    
    # 3️⃣ 数据库没有数据，直接调用VOS API
    logger.info(f'本地数据库无数据，从VOS {instance.name} 获取客户列表')
    client = VOSClient(instance.base_url)
    try:
        result = client.call_api('/external/server/GetAllCustomers', {'type': 1})
        
        if not client.is_success(result):
            error_msg = client.get_error_message(result)
            logger.error(f'VOS {instance.name} API调用失败: {error_msg}')
            # 触发后台同步（可能是暂时的网络问题）
            sync_customers_for_instance.delay(instance_id)
            return {
                'customers': [],
                'count': 0,
                'error': error_msg,
                'instance_id': instance_id,
                'instance_name': instance.name,
                'from_cache': False,
                'data_source': 'vos_api_failed',
                'message': 'VOS API错误，后台同步已触发'
            }
        
        # VOS API 调用成功，立即保存到数据库
        customers_data = result.get('infoCustomerBriefs', [])
        logger.info(f'从VOS {instance.name} 获取到 {len(customers_data)} 个客户，开始保存到数据库')
        
        # 同步保存到数据库（同步执行，确保立即可用）
        for cust_data in customers_data:
            account = cust_data.get('account')
            if not account:
                continue
            
            money = float(cust_data.get('money', 0.0))
            limit_money = float(cust_data.get('limitMoney', 0.0))
            is_in_debt = money < 0
            
            # 将完整的VOS客户数据保存为JSON字符串
            raw_data_json = json.dumps(cust_data, ensure_ascii=False)
            
            new_customer = Customer(
                vos_instance_id=instance_id,
                account=account,
                money=money,
                limit_money=limit_money,
                is_in_debt=is_in_debt,
                raw_data=raw_data_json
            )
            db.add(new_customer)
        
        db.commit()
        logger.info(f'已将 {len(customers_data)} 个客户数据保存到数据库')
        
        # 触发后台同步任务，确保后续数据更新
        sync_customers_for_instance.delay(instance_id)
        
        return {
            'customers': customers_data,
            'count': len(customers_data),
            'instance_id': instance_id,
            'instance_name': instance.name,
            'from_cache': False,
            'data_source': 'vos_api',
            'message': '数据已从VOS获取并保存到数据库，后台同步已启动'
        }
        
    except Exception as e:
        logger.error(f'从VOS {instance.name} 获取客户数据失败: {e}')
        # VOS调用失败，触发后台同步
        sync_customers_for_instance.delay(instance_id)
        raise HTTPException(
            status_code=500,
            detail=f'从VOS获取客户数据失败: {str(e)}'
        )

@router.get('/customers/summary')
async def get_all_customers_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """获取所有启用的 VOS 实例的客户总数（从本地数据库读取）"""
    try:
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        
        total_customers = 0
        instance_summaries = []
        
        for instance in instances:
            # 从本地数据库统计客户数量
            count = db.query(Customer).filter(
                Customer.vos_instance_id == instance.id
            ).count()
            
            total_customers += count
            
            instance_summaries.append({
                'instance_id': instance.id,
                'instance_name': instance.name,
                'customer_count': count
            })
        
        return {
            'total_customers': total_customers,
            'instances': instance_summaries,
            'instance_count': len(instances),
            'from_cache': True
        }
    except Exception as e:
        logger.error(f'获取客户统计失败: {e}')
        return {
            'total_customers': 0,
            'instances': [],
            'instance_count': 0,
            'from_cache': True,
            'error': str(e)
        }


@router.get('/customers/debt-count')
async def get_debt_customers_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """获取欠费客户数量"""
    try:
        # 从本地数据库统计欠费客户数量
        debt_count = db.query(Customer).filter(
            Customer.is_in_debt == True
        ).count()
        
        return {
            'debt_count': debt_count,
            'success': True
        }
    except Exception as e:
        logger.error(f'获取欠费客户数量失败: {e}')
        return {
            'debt_count': 0,
            'success': False,
            'error': str(e)
        }


@router.post('/instances/{instance_id}/sync-customers')
async def manual_sync_customers(
    instance_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """手动触发客户数据同步"""
    instance = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail='Instance not found')
    
    # 触发异步同步任务
    sync_customers_for_instance.delay(instance_id)
    
    return {
        'message': f'Customer data sync has been triggered for {instance.name}',
        'instance_id': instance_id,
        'instance_name': instance.name
    }


@router.get('/instances/health/status')
async def get_all_instances_health(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """获取所有VOS实例的健康状态"""
    instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
    
    results = []
    for inst in instances:
        health_check = db.query(VOSHealthCheck).filter(
            VOSHealthCheck.vos_instance_id == inst.id
        ).first()
        
        results.append({
            'instance_id': inst.id,
            'instance_name': inst.name,
            'status': health_check.status if health_check else 'unknown',
            'last_check_at': health_check.last_check_at.isoformat() if health_check and health_check.last_check_at else None,
            'response_time_ms': health_check.response_time_ms if health_check else None,
            'consecutive_failures': health_check.consecutive_failures if health_check else 0,
            'error_message': health_check.error_message if health_check else None
        })
    
    return {'instances': results}


@router.post('/instances/health/check')
async def trigger_health_check(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """手动触发VOS实例健康检查"""
    # 触发异步健康检查任务
    check_vos_instances_health.delay()
    
    return {
        'message': 'VOS实例健康检查已触发',
        'status': 'triggered'
    }

