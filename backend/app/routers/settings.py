from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.app_config import AppConfig
from typing import Dict, Any

router = APIRouter(prefix='/settings', tags=['settings'])


@router.get('/notification', response_model=Dict[str, Any])
async def get_notification_settings(db: Session = Depends(get_db)):
    """
    获取通知配置
    """
    configs = db.query(AppConfig).filter(
        AppConfig.config_key.in_([
            'notification_bark_url',
            'notification_email_smtp_server',
            'notification_email_smtp_port',
            'notification_email_username',
            'notification_email_password',
            'notification_email_from',
            'notification_email_to'
        ])
    ).all()
    
    # 将配置转换为字典
    result = {
        'bark_url': '',
        'email_smtp_server': '',
        'email_smtp_port': '',
        'email_username': '',
        'email_password': '',
        'email_from': '',
        'email_to': ''
    }
    
    for config in configs:
        if config.config_key == 'notification_bark_url':
            result['bark_url'] = config.config_value or ''
        elif config.config_key == 'notification_email_smtp_server':
            result['email_smtp_server'] = config.config_value or ''
        elif config.config_key == 'notification_email_smtp_port':
            result['email_smtp_port'] = config.config_value or ''
        elif config.config_key == 'notification_email_username':
            result['email_username'] = config.config_value or ''
        elif config.config_key == 'notification_email_password':
            result['email_password'] = config.config_value or ''
        elif config.config_key == 'notification_email_from':
            result['email_from'] = config.config_value or ''
        elif config.config_key == 'notification_email_to':
            result['email_to'] = config.config_value or ''
    
    return result


@router.post('/notification')
async def save_notification_settings(
    configs: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    保存通知配置
    """
    # 配置映射关系
    config_mapping = {
        'bark_url': 'notification_bark_url',
        'email_smtp_server': 'notification_email_smtp_server',
        'email_smtp_port': 'notification_email_smtp_port',
        'email_username': 'notification_email_username',
        'email_password': 'notification_email_password',
        'email_from': 'notification_email_from',
        'email_to': 'notification_email_to'
    }
    
    # 保存配置
    for key, value in configs.items():
        if key in config_mapping:
            config_key = config_mapping[key]
            # 查找现有配置
            existing = db.query(AppConfig).filter(AppConfig.config_key == config_key).first()
            if existing:
                # 更新现有配置
                existing.config_value = value
            else:
                # 创建新配置
                new_config = AppConfig(
                    config_key=config_key,
                    config_value=value,
                    description=f'通知配置: {key}'
                )
                db.add(new_config)
    
    db.commit()
    return {'success': True, 'message': '通知配置保存成功'}