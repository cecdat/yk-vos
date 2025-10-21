from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text
from app.models.base import Base
class CDR(Base):
    __tablename__ = 'cdrs'
    id = Column(Integer, primary_key=True, index=True)
    vos_id = Column(Integer, index=True)
    caller = Column(String(64))
    callee = Column(String(64))
    caller_gateway = Column(String(64))
    callee_gateway = Column(String(64))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Integer)
    cost = Column(Numeric(10,4))
    disposition = Column(String(64))
    raw = Column(Text)
    hash = Column(String(32), index=True)
