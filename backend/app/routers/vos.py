from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.vos_client import VOSClient
from app.models.user import User
from app.models.vos_instance import VOSInstance
from app.models.phone import Phone
from app.routers.auth import get_current_user

router = APIRouter(prefix='/vos', tags=['vos'])

@router.get('/instances')
async def get_instances(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
    return [
        {
            'id': inst.id,
            'name': inst.name,
            'base_url': inst.base_url,
            'description': inst.description,
            'enabled': inst.enabled
        }
        for inst in instances
    ]

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
    
    # Get from VOS API
    client = VOSClient(instance.base_url)
    res = client.post('/external/server/GetPhoneOnline', payload={})
    
    # Try different response formats
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

