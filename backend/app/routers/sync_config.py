"""
同步配置管理路由
"""
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from app.core.db import get_db
from app.models.user import User
from app.models.sync_config import SyncConfig
from app.routers.auth import get_current_user

router = APIRouter(prefix='/sync-config', tags=['sync-config'])
logger = logging.getLogger(__name__)


class SyncConfigCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cron_expression: str
    enabled: bool = True
    sync_type: str  # customers, cdrs, phones, all


class SyncConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    enabled: Optional[bool] = None
    sync_type: Optional[str] = None


@router.get('/configs')
async def get_sync_configs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """获取所有同步配置"""
    configs = db.query(SyncConfig).all()
    
    return {
        'success': True,
        'configs': [
            {
                'id': c.id,
                'name': c.name,
                'description': c.description,
                'cron_expression': c.cron_expression,
                'enabled': c.enabled,
                'sync_type': c.sync_type,
                'created_at': c.created_at.isoformat() if c.created_at else None,
                'updated_at': c.updated_at.isoformat() if c.updated_at else None
            }
            for c in configs
        ]
    }


@router.get('/configs/{config_id}')
async def get_sync_config(
    config_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """获取单个同步配置"""
    config = db.query(SyncConfig).filter(SyncConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail='配置未找到')
    
    return {
        'success': True,
        'config': {
            'id': config.id,
            'name': config.name,
            'description': config.description,
            'cron_expression': config.cron_expression,
            'enabled': config.enabled,
            'sync_type': config.sync_type,
            'created_at': config.created_at.isoformat() if config.created_at else None,
            'updated_at': config.updated_at.isoformat() if config.updated_at else None
        }
    }


@router.post('/configs')
async def create_sync_config(
    config_data: SyncConfigCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """创建同步配置"""
    # 检查名称是否已存在
    existing = db.query(SyncConfig).filter(SyncConfig.name == config_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail='配置名称已存在')
    
    # 验证同步类型
    valid_types = ['customers', 'cdrs', 'phones', 'all']
    if config_data.sync_type not in valid_types:
        raise HTTPException(status_code=400, detail=f'同步类型必须是: {", ".join(valid_types)}')
    
    new_config = SyncConfig(
        name=config_data.name,
        description=config_data.description,
        cron_expression=config_data.cron_expression,
        enabled=config_data.enabled,
        sync_type=config_data.sync_type
    )
    
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    
    logger.info(f'创建同步配置: {new_config.name}')
    
    return {
        'success': True,
        'message': '同步配置创建成功',
        'config': {
            'id': new_config.id,
            'name': new_config.name,
            'description': new_config.description,
            'cron_expression': new_config.cron_expression,
            'enabled': new_config.enabled,
            'sync_type': new_config.sync_type
        }
    }


@router.put('/configs/{config_id}')
async def update_sync_config(
    config_id: int,
    config_data: SyncConfigUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """更新同步配置"""
    config = db.query(SyncConfig).filter(SyncConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail='配置未找到')
    
    # 更新字段
    if config_data.name is not None:
        # 检查新名称是否与其他配置冲突
        existing = db.query(SyncConfig).filter(
            SyncConfig.name == config_data.name,
            SyncConfig.id != config_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail='配置名称已存在')
        config.name = config_data.name
    
    if config_data.description is not None:
        config.description = config_data.description
    
    if config_data.cron_expression is not None:
        config.cron_expression = config_data.cron_expression
    
    if config_data.enabled is not None:
        config.enabled = config_data.enabled
    
    if config_data.sync_type is not None:
        valid_types = ['customers', 'cdrs', 'phones', 'all']
        if config_data.sync_type not in valid_types:
            raise HTTPException(status_code=400, detail=f'同步类型必须是: {", ".join(valid_types)}')
        config.sync_type = config_data.sync_type
    
    db.commit()
    db.refresh(config)
    
    logger.info(f'更新同步配置: {config.name}')
    
    return {
        'success': True,
        'message': '同步配置更新成功',
        'config': {
            'id': config.id,
            'name': config.name,
            'description': config.description,
            'cron_expression': config.cron_expression,
            'enabled': config.enabled,
            'sync_type': config.sync_type
        }
    }


@router.delete('/configs/{config_id}')
async def delete_sync_config(
    config_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """删除同步配置"""
    config = db.query(SyncConfig).filter(SyncConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail='配置未找到')
    
    config_name = config.name
    db.delete(config)
    db.commit()
    
    logger.info(f'删除同步配置: {config_name}')
    
    return {
        'success': True,
        'message': '同步配置删除成功'
    }

