from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.models.base import Base

class Phone(Base):
    __tablename__ = 'phones'
    
    id = Column(Integer, primary_key=True, index=True)
    e164 = Column(String(64), index=True)
    status = Column(String(64))
    last_seen = Column(DateTime, default=datetime.utcnow)
    vos_id = Column(Integer, index=True)

