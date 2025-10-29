from sqlalchemy import Column, Integer, String, Text, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
import uuid

class VOSInstance(Base):
    __tablename__ = 'vos_instances'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_uuid = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False)
    base_url = Column(String(256), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    api_user = Column(String(128))
    api_password = Column(String(128))
    
    # 确保UUID唯一性
    __table_args__ = (
        UniqueConstraint('vos_uuid', name='uq_vos_instances_uuid'),
    )

