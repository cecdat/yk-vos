"""Generic VOS data cache model for all VOS API responses"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.models.base import Base
from datetime import datetime, timedelta


class VosDataCache(Base):
    """
    通用的 VOS 数据缓存表
    用于存储所有 VOS API 接口的响应数据
    """
    __tablename__ = 'vos_data_cache'
    
    id = Column(Integer, primary_key=True, index=True)
    vos_instance_id = Column(Integer, ForeignKey('vos_instances.id'), nullable=False, index=True)
    
    # API 标识
    api_path = Column(String(255), nullable=False, index=True)  # 例如: /external/server/GetCustomer
    api_name = Column(String(128), nullable=True)  # 例如: GetCustomer (便于识别)
    
    # 缓存键（用于区分同一接口的不同查询参数）
    cache_key = Column(String(255), nullable=False, index=True)  # MD5(api_path + params)
    
    # 查询参数（JSON格式，用于调试和重新查询）
    query_params = Column(JSONB, nullable=True)
    
    # 响应数据（完整的VOS API响应）
    response_data = Column(JSONB, nullable=False)
    
    # 状态信息
    is_valid = Column(Boolean, default=True, index=True)  # 数据是否有效
    ret_code = Column(Integer, default=0)  # VOS返回码
    error_message = Column(Text, nullable=True)  # 错误信息（如果有）
    
    # 时间戳
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # 最后同步时间
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)  # 过期时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 复合索引：提高查询性能
    __table_args__ = (
        # 快速查找特定VOS实例的特定API的缓存
        Index('idx_vos_api_cache', 'vos_instance_id', 'api_path', 'cache_key', unique=True),
        # 快速查找有效的缓存数据
        Index('idx_vos_cache_valid', 'vos_instance_id', 'is_valid', 'expires_at'),
        # 快速清理过期数据
        Index('idx_vos_cache_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<VosDataCache {self.api_name or self.api_path} (VOS#{self.vos_instance_id}, key={self.cache_key[:8]})>"
    
    def is_expired(self) -> bool:
        """检查缓存是否已过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def get_cache_ttl(cls, api_path: str) -> int:
        """
        根据API路径返回建议的缓存时间（秒）
        
        实时数据：30秒
        准实时数据：5分钟
        历史数据：1小时
        配置数据：24小时
        """
        # 实时数据（30秒）
        realtime_apis = [
            '/external/server/GetPhoneOnline',
            '/external/server/GetAllPhoneOnline',
            '/external/server/GetCurrentCall',
            '/external/server/GetGatewayMappingOnline',
            '/external/server/GetGatewayRoutingOnline',
            '/external/server/GetPerformance',
            '/external/server/GetAlarmCurrent',
        ]
        
        # 准实时数据（5分钟）
        semi_realtime_apis = [
            '/external/server/GetAllCustomers',
            '/external/server/GetCustomer',
            '/external/server/GetPhone',
        ]
        
        # 历史数据（1小时）
        historical_apis = [
            '/external/server/GetCdr',
            '/external/server/GetPayHistory',
            '/external/server/GetConsumption',
        ]
        
        # 配置数据（24小时）
        config_apis = [
            '/external/server/GetGatewayMapping',
            '/external/server/GetGatewayRouting',
            '/external/server/GetFeeRateGroup',
            '/external/server/GetFeeRate',
            '/external/server/GetSuite',
            '/external/server/GetSoftSwitch',
            '/external/server/GetE164Convert',
            '/external/server/GetIvrAudio',
        ]
        
        if api_path in realtime_apis:
            return 30  # 30秒
        elif api_path in semi_realtime_apis:
            return 300  # 5分钟
        elif api_path in historical_apis:
            return 3600  # 1小时
        elif api_path in config_apis:
            return 86400  # 24小时
        else:
            return 300  # 默认5分钟

