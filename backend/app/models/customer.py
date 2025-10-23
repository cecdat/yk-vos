"""Customer model for storing VOS customer data"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.sql import func
from app.models.base import Base


class Customer(Base):
    """VOS客户信息表"""
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_instance_id = Column(Integer, ForeignKey('vos_instances.id'), nullable=False, index=True)
    
    # 客户基本信息
    account = Column(String(255), nullable=False, index=True)  # 客户账号
    money = Column(Float, default=0.0)  # 当前余额
    limit_money = Column(Float, default=0.0)  # 授信额度
    
    # 状态标记
    is_in_debt = Column(Boolean, default=False, index=True)  # 是否欠费 (money < 0)
    
    # 存储VOS返回的完整原始数据（JSON格式）
    raw_data = Column(Text, nullable=True)  # VOS接口返回的完整客户数据
    
    # 时间戳
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # 最后同步时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 复合索引：快速查询某个VOS实例的客户
    __table_args__ = (
        Index('idx_vos_account', 'vos_instance_id', 'account'),
        Index('idx_vos_debt', 'vos_instance_id', 'is_in_debt'),
    )
    
    def __repr__(self):
        return f"<Customer {self.account} (VOS#{self.vos_instance_id})>"

