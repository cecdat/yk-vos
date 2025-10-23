"""Enhanced Phone model with more fields"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.models.base import Base


class PhoneEnhanced(Base):
    """增强版话机信息表"""
    __tablename__ = 'phones_enhanced'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_instance_id = Column(Integer, ForeignKey('vos_instances.id'), nullable=False, index=True)
    
    # 话机基本信息
    e164 = Column(String(64), nullable=False, index=True)  # 话机号码
    account = Column(String(255), index=True)  # 所属账户
    
    # 在线状态
    is_online = Column(Boolean, default=False, index=True)
    register_time = Column(DateTime(timezone=True))  # 注册时间
    last_seen = Column(DateTime(timezone=True))  # 最后在线时间
    
    # 话机配置
    ip_address = Column(String(100))  # IP地址
    port = Column(Integer)  # 端口
    user_agent = Column(String(255))  # User Agent
    
    # 通话统计
    total_calls = Column(Integer, default=0)  # 总通话次数
    total_duration = Column(Integer, default=0)  # 总通话时长（秒）
    last_call_time = Column(DateTime(timezone=True))  # 最后通话时间
    
    # 余额信息（快照）
    balance = Column(Float, default=0.0)
    
    # 存储完整的VOS原始数据
    raw_data = Column(JSONB, nullable=True)
    
    # 时间戳
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 复合索引
    __table_args__ = (
        Index('idx_phone_vos_e164', 'vos_instance_id', 'e164', unique=True),
        Index('idx_phone_account', 'vos_instance_id', 'account'),
        Index('idx_phone_online', 'vos_instance_id', 'is_online'),
    )
    
    def __repr__(self):
        return f"<PhoneEnhanced {self.e164} (online={self.is_online})>"

