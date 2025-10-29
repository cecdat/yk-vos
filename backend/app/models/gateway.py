"""Gateway models for VOS gateway data"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from app.models.base import Base


class Gateway(Base):
    """VOS网关信息表（对接网关 + 落地网关）"""
    __tablename__ = 'gateways'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_instance_id = Column(Integer, ForeignKey('vos_instances.id'), nullable=False, index=True)
    vos_uuid = Column(UUID(as_uuid=True), nullable=True, index=True)  # VOS节点唯一标识
    
    # 网关基本信息
    gateway_name = Column(String(255), nullable=False, index=True)  # 网关名称
    gateway_type = Column(String(50), nullable=False, index=True)  # mapping(对接) 或 routing(落地)
    
    # 网关配置
    ip_address = Column(String(100))  # IP地址
    port = Column(Integer)  # 端口
    protocol = Column(String(50))  # 协议类型
    
    # 在线状态
    is_online = Column(Boolean, default=False, index=True)
    
    # 性能指标
    asr = Column(Float, default=0.0)  # 应答率
    acd = Column(Float, default=0.0)  # 平均通话时长
    concurrent_calls = Column(Integer, default=0)  # 当前并发数
    
    # 存储完整的VOS原始数据
    raw_data = Column(JSONB, nullable=True)
    
    # 时间戳
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 复合索引
    __table_args__ = (
        Index('idx_gateway_vos_name', 'vos_instance_id', 'gateway_name', unique=True),
        Index('idx_gateway_online', 'vos_instance_id', 'is_online'),
        Index('idx_gateway_type', 'vos_instance_id', 'gateway_type'),
    )
    
    def __repr__(self):
        return f"<Gateway {self.gateway_name} ({self.gateway_type})>"


class FeeRateGroup(Base):
    """费率组表"""
    __tablename__ = 'fee_rate_groups'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_instance_id = Column(Integer, ForeignKey('vos_instances.id'), nullable=False, index=True)
    
    # 费率组信息
    group_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # 存储完整配置
    raw_data = Column(JSONB, nullable=True)
    
    # 时间戳
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_feerate_vos_name', 'vos_instance_id', 'group_name', unique=True),
    )
    
    def __repr__(self):
        return f"<FeeRateGroup {self.group_name}>"


class Suite(Base):
    """套餐表"""
    __tablename__ = 'suites'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_instance_id = Column(Integer, ForeignKey('vos_instances.id'), nullable=False, index=True)
    
    # 套餐信息
    suite_id = Column(String(100), nullable=False, index=True)  # VOS中的套餐ID
    suite_name = Column(String(255))
    suite_type = Column(String(100))
    
    # 费用信息
    price = Column(Float, default=0.0)
    monthly_fee = Column(Float, default=0.0)
    
    # 套餐内容
    duration = Column(Integer, default=0)  # 时长（分钟）
    
    # 存储完整配置
    raw_data = Column(JSONB, nullable=True)
    
    # 时间戳
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_suite_vos_id', 'vos_instance_id', 'suite_id', unique=True),
    )
    
    def __repr__(self):
        return f"<Suite {self.suite_name}>"

