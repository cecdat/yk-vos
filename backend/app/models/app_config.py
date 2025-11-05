"""
应用配置模型
用于存储简单的键值对配置
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class AppConfig(Base):
    """应用配置表"""
    __tablename__ = 'app_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True, comment='配置键')
    config_value = Column(String(500), nullable=True, comment='配置值')
    description = Column(String(500), comment='配置描述')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AppConfig(key='{self.config_key}', value='{self.config_value}')>"

