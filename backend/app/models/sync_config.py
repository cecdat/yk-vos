"""
数据同步配置模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.db import Base


class SyncConfig(Base):
    """数据同步配置表"""
    __tablename__ = 'sync_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 配置名称和描述
    name = Column(String(100), unique=True, nullable=False, index=True, comment='配置名称')
    description = Column(String(500), comment='配置描述')
    
    # Cron表达式
    cron_expression = Column(String(100), nullable=False, comment='Cron表达式')
    
    # 是否启用
    enabled = Column(Boolean, default=True, nullable=False, comment='是否启用')
    
    # 同步类型
    sync_type = Column(String(50), nullable=False, comment='同步类型：customers|cdrs|phones|all')
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SyncConfig(name='{self.name}', type='{self.sync_type}', cron='{self.cron_expression}')>"

