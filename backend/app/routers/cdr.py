from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.db import get_db
from app.models.user import User
from app.models.cdr import CDR
from app.routers.auth import get_current_user

router = APIRouter(prefix='/cdr', tags=['cdr'])

@router.get('/history')
async def get_cdr_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    vos_id: Optional[int] = None,
    limit: int = Query(default=100, le=1000)
):
    query = db.query(CDR)
    
    if vos_id:
        query = query.filter(CDR.vos_id == vos_id)
    
    cdrs = query.order_by(desc(CDR.start_time)).limit(limit).all()
    
    return [
        {
            'id': cdr.id,
            'vos_id': cdr.vos_id,
            'caller': cdr.caller,
            'callee': cdr.callee,
            'caller_gateway': cdr.caller_gateway,
            'callee_gateway': cdr.callee_gateway,
            'start_time': cdr.start_time.isoformat() if cdr.start_time else None,
            'end_time': cdr.end_time.isoformat() if cdr.end_time else None,
            'duration': cdr.duration,
            'cost': float(cdr.cost) if cdr.cost else 0,
            'disposition': cdr.disposition,
        }
        for cdr in cdrs
    ]

@router.get('/stats')
async def get_cdr_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    vos_id: Optional[int] = None
):
    query = db.query(CDR)
    
    if vos_id:
        query = query.filter(CDR.vos_id == vos_id)
    
    total_count = query.count()
    total_duration = db.query(func.sum(CDR.duration)).filter(
        CDR.vos_id == vos_id if vos_id else True
    ).scalar() or 0
    
    return {
        'total_count': total_count,
        'total_duration': total_duration,
        'vos_id': vos_id
    }

