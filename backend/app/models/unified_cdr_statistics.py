"""
统一的话单费用统计模型
合并VOS节点、账户、网关三个级别的统计数据到一张表
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, BigInteger, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from datetime import datetime


class UnifiedCdrStatistics(Base):
    """统一的话单费用统计表"""
    __tablename__ = 'cdr_statistics'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基础关联字段
    vos_id = Column(Integer, nullable=False, index=True, comment='VOS实例ID')
    vos_uuid = Column(UUID(as_uuid=True), nullable=False, index=True, comment='VOS节点UUID')
    statistic_date = Column(Date, nullable=False, index=True, comment='统计日期')
    period_type = Column(String(10), nullable=False, index=True, comment='统计周期：day, month, quarter, year')
    
    # 统计维度类型
    statistic_type = Column(String(20), nullable=False, index=True, comment='统计类型：vos, account, gateway')
    
    # 维度标识字段（根据 statistic_type 使用不同的字段）
    # 当 statistic_type = 'vos' 时，dimension_value 为空
    # 当 statistic_type = 'account' 时，dimension_value 存储账户名称
    # 当 statistic_type = 'gateway' 时，dimension_value 存储网关名称
    dimension_value = Column(String(256), nullable=True, index=True, comment='维度值：账户名称或网关名称')
    
    # 统计指标
    total_fee = Column(Numeric(15, 4), default=0, comment='总费用')
    total_duration = Column(BigInteger, default=0, comment='总通话时长（秒，大于0秒的通话）')
    total_calls = Column(BigInteger, default=0, comment='总通话记录数')
    connected_calls = Column(BigInteger, default=0, comment='接通通话数（hold_time > 0）')
    connection_rate = Column(Numeric(5, 2), default=0, comment='接通率（百分比）')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('vos_uuid', 'statistic_type', 'dimension_value', 'statistic_date', 'period_type', 
                        name='uq_cdr_statistics'),
        Index('idx_cdr_statistics_vos_composite', 'vos_uuid', 'statistic_date', 'period_type', 'statistic_type'),
    )
    
    def __repr__(self):
        return f"<UnifiedCdrStatistics(vos_id={self.vos_id}, type={self.statistic_type}, date={self.statistic_date})>"

