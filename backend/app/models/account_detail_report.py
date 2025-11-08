"""
账户明细报表模型
存储从VOS API获取的账户明细报表数据
"""
from sqlalchemy import Column, Integer, String, Numeric, BigInteger, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.models.base import Base


class AccountDetailReport(Base):
    """账户明细报表表"""
    __tablename__ = 'account_detail_reports'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_instance_id = Column(Integer, ForeignKey('vos_instances.id'), nullable=False, index=True, comment='VOS实例ID')
    vos_uuid = Column(UUID(as_uuid=True), nullable=False, index=True, comment='VOS节点UUID')
    
    # 账户信息
    account = Column(String(255), nullable=False, index=True, comment='账户号码')
    account_name = Column(String(255), nullable=True, comment='账户名称')
    
    # 时间信息（UTC时间戳，毫秒）
    begin_time = Column(BigInteger, nullable=False, index=True, comment='起始时间（UTC 1970-01-01 至今的毫秒数）')
    end_time = Column(BigInteger, nullable=False, index=True, comment='终止时间（UTC 1970-01-01 至今的毫秒数）')
    
    # 统计数据
    cdr_count = Column(BigInteger, default=0, comment='话单总计')
    total_fee = Column(Numeric(15, 4), default=0, comment='费用总计')
    total_time = Column(BigInteger, default=0, comment='计费时长总计（秒）')
    total_suite_fee = Column(Numeric(15, 4), default=0, comment='套餐费用总计')
    total_suite_fee_time = Column(BigInteger, default=0, comment='套餐费用时长')
    
    # 网络费用（暂时保留，可能为0）
    net_fee = Column(Numeric(15, 4), default=0, comment='网络费用')
    net_time = Column(BigInteger, default=0, comment='网络时长')
    net_count = Column(BigInteger, default=0, comment='网络数量')
    
    # 本地费用（暂时保留，可能为0）
    local_fee = Column(Numeric(15, 4), default=0, comment='本地费用')
    local_time = Column(BigInteger, default=0, comment='本地时长')
    local_count = Column(BigInteger, default=0, comment='本地数量')
    
    # 国内费用
    domestic_fee = Column(Numeric(15, 4), default=0, comment='国内通话费用')
    domestic_time = Column(BigInteger, default=0, comment='国内通话计费时长（秒）')
    domestic_count = Column(BigInteger, default=0, comment='国内通话数量')
    
    # 国际费用（暂时保留，可能为0）
    international_fee = Column(Numeric(15, 4), default=0, comment='国际费用')
    international_time = Column(BigInteger, default=0, comment='国际时长')
    international_count = Column(BigInteger, default=0, comment='国际数量')
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 唯一约束：同一个VOS实例、账户、时间段的报表只能有一条记录
    __table_args__ = (
        UniqueConstraint('vos_instance_id', 'vos_uuid', 'account', 'begin_time', 'end_time', 
                        name='uq_account_detail_report'),
        Index('idx_account_detail_report_vos_account', 'vos_instance_id', 'vos_uuid', 'account'),
        Index('idx_account_detail_report_time', 'begin_time', 'end_time'),
        Index('idx_account_detail_report_account_time', 'account', 'begin_time', 'end_time'),
    )
    
    def __repr__(self):
        return f"<AccountDetailReport {self.account} ({self.begin_time}-{self.end_time})>"

