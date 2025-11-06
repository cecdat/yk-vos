"""
话单费用统计模型
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, BigInteger, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from datetime import datetime


class VOSCdrStatistics(Base):
    """VOS节点级别的话单统计"""
    __tablename__ = 'vos_cdr_statistics'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_id = Column(Integer, nullable=False, index=True, comment='VOS实例ID')
    vos_uuid = Column(UUID(as_uuid=True), nullable=False, index=True, comment='VOS节点UUID')
    statistic_date = Column(Date, nullable=False, index=True, comment='统计日期')
    period_type = Column(String(10), nullable=False, index=True, comment='统计周期：day, month, quarter, year')
    
    # 费用统计
    total_fee = Column(Numeric(15, 4), default=0, comment='总费用')
    
    # 时长统计
    total_duration = Column(BigInteger, default=0, comment='总通话时长（秒，大于0秒的通话）')
    total_calls = Column(BigInteger, default=0, comment='总通话记录数')
    connected_calls = Column(BigInteger, default=0, comment='接通通话数（hold_time > 0）')
    
    # 接通率
    connection_rate = Column(Numeric(5, 2), default=0, comment='接通率（百分比）')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('vos_id', 'vos_uuid', 'statistic_date', 'period_type', name='uq_vos_cdr_statistics'),
        Index('idx_vos_cdr_statistics_composite', 'vos_uuid', 'statistic_date', 'period_type'),
    )


class AccountCdrStatistics(Base):
    """账户级别的话单统计"""
    __tablename__ = 'account_cdr_statistics'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_id = Column(Integer, nullable=False, index=True)
    vos_uuid = Column(UUID(as_uuid=True), nullable=False, index=True)
    account_name = Column(String(256), nullable=False, index=True, comment='账户名称')
    statistic_date = Column(Date, nullable=False, index=True)
    period_type = Column(String(10), nullable=False, index=True)
    
    total_fee = Column(Numeric(15, 4), default=0)
    total_duration = Column(BigInteger, default=0)
    total_calls = Column(BigInteger, default=0)
    connected_calls = Column(BigInteger, default=0)
    connection_rate = Column(Numeric(5, 2), default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('vos_id', 'vos_uuid', 'account_name', 'statistic_date', 'period_type', name='uq_account_cdr_statistics'),
        Index('idx_account_cdr_statistics_composite', 'vos_uuid', 'account_name', 'statistic_date', 'period_type'),
    )


class GatewayCdrStatistics(Base):
    """网关级别的话单统计"""
    __tablename__ = 'gateway_cdr_statistics'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_id = Column(Integer, nullable=False, index=True)
    vos_uuid = Column(UUID(as_uuid=True), nullable=False, index=True)
    gateway_name = Column(String(256), nullable=False, index=True, comment='网关名称')
    gateway_type = Column(String(20), nullable=False, index=True, comment='网关类型：caller（对接网关）或callee（落地网关）')
    statistic_date = Column(Date, nullable=False, index=True)
    period_type = Column(String(10), nullable=False, index=True)
    
    total_fee = Column(Numeric(15, 4), default=0)
    total_duration = Column(BigInteger, default=0)
    total_calls = Column(BigInteger, default=0)
    connected_calls = Column(BigInteger, default=0)
    connection_rate = Column(Numeric(5, 2), default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('vos_id', 'vos_uuid', 'gateway_name', 'gateway_type', 'statistic_date', 'period_type', name='uq_gateway_cdr_statistics'),
        Index('idx_gateway_cdr_statistics_composite', 'vos_uuid', 'gateway_name', 'gateway_type', 'statistic_date', 'period_type'),
    )

