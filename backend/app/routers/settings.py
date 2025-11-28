import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.app_config import AppConfig
from typing import Dict, Any

logger = logging.getLogger(__name__)

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
            'notification_email_to',
            'notification_push_projects',
            'notification_push_types'
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
        'email_to': '',
        'push_projects': 'all',
        'push_types': 'all'
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
        elif config.config_key == 'notification_push_projects':
            result['push_projects'] = config.config_value or 'all'
        elif config.config_key == 'notification_push_types':
            result['push_types'] = config.config_value or 'all'
    
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
        'email_to': 'notification_email_to',
        'push_projects': 'notification_push_projects',
        'push_types': 'notification_push_types'
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


@router.post('/notification/test')
async def test_notification(
    notification_type: str = Query('all', description='通知类型，可选值：all, bark, email'),
    db: Session = Depends(get_db)
):
    """
    测试通知推送
    
    Args:
        notification_type: 通知类型，可选值：all, bark, email
    """
    from app.core.notification_service import get_notification_service
    
    try:
        # 获取通知服务实例
        notification_service = get_notification_service(db)
        
        # 发送测试通知
        sync_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        title = f"测试通知 - {sync_date}"
        content = "这是一条测试通知，用于验证推送配置是否正确。"
        
        # 获取发送结果
        results = notification_service.send_notification(title, content, notification_type)
        
        # 检查发送结果
        if notification_type == 'all':
            # 检查所有发送的通知类型是否成功
            success = all(result['success'] for result in results.values() if result['message'] != '未配置或未发送')
            messages = [f"{type}: {result['message']}" for type, result in results.items() if result['message'] != '未配置或未发送']
        else:
            # 只检查指定类型的通知是否成功
            result = results[notification_type]
            success = result['success']
            messages = [result['message']]
        
        return {
            'success': success,
            'message': '; '.join(messages),
            'title': title,
            'content': content,
            'results': results
        }
    except Exception as e:
        logger.error(f'测试通知发送失败: {e}')
        return {
            'success': False,
            'message': f'测试通知发送失败: {str(e)}'
        }