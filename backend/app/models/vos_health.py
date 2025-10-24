from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.models.base import Base


class VOSHealthCheck(Base):
    """VOS实例健康检查记录"""
    __tablename__ = 'vos_health_checks'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_instance_id = Column(Integer, ForeignKey('vos_instances.id'), nullable=False, index=True)
    
    # 健康状态: healthy, unhealthy, unknown
    status = Column(String(20), default='unknown')
    
    # 最后一次检查时间
    last_check_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 响应时间 (毫秒)
    response_time_ms = Column(Float, nullable=True)
    
    # 错误信息 (如果有)
    error_message = Column(String(500), nullable=True)
    
    # API调用是否成功
    api_success = Column(Boolean, default=False)
    
    # 连续失败次数
    consecutive_failures = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

