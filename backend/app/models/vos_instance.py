from sqlalchemy import Column, Integer, String, Text, Boolean
from app.models.base import Base

class VOSInstance(Base):
    __tablename__ = 'vos_instances'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    base_url = Column(String(256), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    api_user = Column(String(128))
    api_password = Column(String(128))

