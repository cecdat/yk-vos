"""
VOS 缓存服务层
实现三级缓存机制：Redis → PostgreSQL → VOS API
"""
import json
import hashlib
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.vos_data_cache import VosDataCache
from app.models.vos_instance import VOSInstance
from app.core.vos_client import VOSClient

logger = logging.getLogger(__name__)


class VosCacheService:
    """VOS数据缓存服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def generate_cache_key(api_path: str, params: Dict[str, Any]) -> str:
        """
        生成缓存键
        基于API路径和参数生成唯一的缓存键
        """
        # 将参数排序后序列化，确保相同参数生成相同的键
        sorted_params = json.dumps(params, sort_keys=True, ensure_ascii=False)
        key_string = f"{api_path}:{sorted_params}"
        
        # 使用 MD5 生成固定长度的缓存键
        cache_key = hashlib.md5(key_string.encode('utf-8')).hexdigest()
        return cache_key
    
    @staticmethod
    def extract_api_name(api_path: str) -> str:
        """从API路径提取接口名称"""
        # 例如: /external/server/GetCustomer -> GetCustomer
        parts = api_path.strip('/').split('/')
        return parts[-1] if parts else api_path
    
    def get_cached_data(
        self,
        vos_instance_id: int,
        api_path: str,
        params: Dict[str, Any],
        force_refresh: bool = False
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        获取缓存数据（三级查询）
        
        Args:
            vos_instance_id: VOS实例ID
            api_path: API路径
            params: 查询参数
            force_refresh: 是否强制刷新
            
        Returns:
            (data, source) 元组
            - data: 响应数据，如果没有则返回None
            - source: 数据来源 ('redis', 'database', 'vos_api', 'error')
        """
        cache_key = self.generate_cache_key(api_path, params)
        
        # 如果强制刷新，直接从VOS获取
        if force_refresh:
            logger.info(f"强制刷新VOS数据: {api_path} (key={cache_key[:8]})")
            return self._fetch_from_vos(vos_instance_id, api_path, params, cache_key)
        
        # 1️⃣ 第一级：尝试从数据库缓存读取
        cached = self.db.query(VosDataCache).filter(
            and_(
                VosDataCache.vos_instance_id == vos_instance_id,
                VosDataCache.api_path == api_path,
                VosDataCache.cache_key == cache_key,
                VosDataCache.is_valid == True
            )
        ).first()
        
        # 如果缓存存在且未过期，直接返回
        if cached and not cached.is_expired():
            logger.info(
                f"从数据库缓存读取: {api_path} "
                f"(key={cache_key[:8]}, age={int((datetime.utcnow() - cached.synced_at).total_seconds())}s)"
            )
            return cached.response_data, 'database'
        
        # 如果缓存过期，记录日志
        if cached:
            logger.info(
                f"缓存已过期: {api_path} "
                f"(key={cache_key[:8]}, expired={int((datetime.utcnow() - cached.expires_at).total_seconds())}s ago)"
            )
        
        # 2️⃣ 第二级：从VOS API获取最新数据
        return self._fetch_from_vos(vos_instance_id, api_path, params, cache_key)
    
    def _fetch_from_vos(
        self,
        vos_instance_id: int,
        api_path: str,
        params: Dict[str, Any],
        cache_key: str
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        从VOS API获取数据并缓存
        """
        # 获取VOS实例
        instance = self.db.query(VOSInstance).filter(
            VOSInstance.id == vos_instance_id
        ).first()
        
        if not instance:
            logger.error(f"VOS实例不存在: {vos_instance_id}")
            return None, 'error'
        
        # 调用VOS API
        logger.info(f"从VOS API获取数据: {api_path} (instance={instance.name})")
        client = VOSClient(instance.base_url)
        
        try:
            result = client.call_api(api_path, params)
            
            # 检查API调用是否成功
            is_success = client.is_success(result)
            ret_code = result.get('retCode', -999)
            error_message = client.get_error_message(result) if not is_success else None
            
            if not is_success:
                logger.warning(
                    f"VOS API调用失败: {api_path} "
                    f"(instance={instance.name}, retCode={ret_code}, error={error_message})"
                )
            
            # 保存到数据库缓存
            self._save_to_cache(
                vos_instance_id=vos_instance_id,
                api_path=api_path,
                cache_key=cache_key,
                params=params,
                response_data=result,
                is_valid=is_success,
                ret_code=ret_code,
                error_message=error_message
            )
            
            if is_success:
                return result, 'vos_api'
            else:
                return None, 'error'
                
        except Exception as e:
            logger.exception(f"从VOS获取数据失败: {api_path} (instance={instance.name}, error={e})")
            return None, 'error'
    
    def _save_to_cache(
        self,
        vos_instance_id: int,
        api_path: str,
        cache_key: str,
        params: Dict[str, Any],
        response_data: Dict[str, Any],
        is_valid: bool,
        ret_code: int,
        error_message: Optional[str]
    ):
        """
        保存数据到缓存
        """
        api_name = self.extract_api_name(api_path)
        
        # 计算过期时间
        ttl = VosDataCache.get_cache_ttl(api_path)
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        # 查找现有缓存
        existing = self.db.query(VosDataCache).filter(
            and_(
                VosDataCache.vos_instance_id == vos_instance_id,
                VosDataCache.api_path == api_path,
                VosDataCache.cache_key == cache_key
            )
        ).first()
        
        if existing:
            # 更新现有缓存
            existing.query_params = params
            existing.response_data = response_data
            existing.is_valid = is_valid
            existing.ret_code = ret_code
            existing.error_message = error_message
            existing.synced_at = datetime.utcnow()
            existing.expires_at = expires_at
            existing.updated_at = datetime.utcnow()
            
            logger.debug(f"更新缓存: {api_name} (key={cache_key[:8]}, ttl={ttl}s)")
        else:
            # 创建新缓存
            new_cache = VosDataCache(
                vos_instance_id=vos_instance_id,
                api_path=api_path,
                api_name=api_name,
                cache_key=cache_key,
                query_params=params,
                response_data=response_data,
                is_valid=is_valid,
                ret_code=ret_code,
                error_message=error_message,
                expires_at=expires_at
            )
            self.db.add(new_cache)
            
            logger.debug(f"创建缓存: {api_name} (key={cache_key[:8]}, ttl={ttl}s)")
        
        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            self.db.rollback()
    
    def invalidate_cache(
        self,
        vos_instance_id: int,
        api_path: Optional[str] = None,
        cache_key: Optional[str] = None
    ):
        """
        使缓存失效
        
        Args:
            vos_instance_id: VOS实例ID
            api_path: API路径（可选，不指定则清除所有）
            cache_key: 缓存键（可选，不指定则清除该API的所有缓存）
        """
        query = self.db.query(VosDataCache).filter(
            VosDataCache.vos_instance_id == vos_instance_id
        )
        
        if api_path:
            query = query.filter(VosDataCache.api_path == api_path)
        
        if cache_key:
            query = query.filter(VosDataCache.cache_key == cache_key)
        
        # 将缓存标记为无效
        count = query.update({'is_valid': False})
        self.db.commit()
        
        logger.info(f"使缓存失效: {count} 条记录 (instance={vos_instance_id}, api={api_path})")
    
    def cleanup_expired_cache(self, days: int = 7):
        """
        清理过期的缓存数据
        
        Args:
            days: 清理多少天前的数据
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 删除过期且无效的缓存
        count = self.db.query(VosDataCache).filter(
            and_(
                VosDataCache.expires_at < cutoff_date,
                VosDataCache.is_valid == False
            )
        ).delete()
        
        self.db.commit()
        
        logger.info(f"清理过期缓存: 删除了 {count} 条记录")
        return count
    
    def get_cache_stats(self, vos_instance_id: int) -> Dict[str, Any]:
        """
        获取缓存统计信息
        """
        total = self.db.query(VosDataCache).filter(
            VosDataCache.vos_instance_id == vos_instance_id
        ).count()
        
        valid = self.db.query(VosDataCache).filter(
            and_(
                VosDataCache.vos_instance_id == vos_instance_id,
                VosDataCache.is_valid == True
            )
        ).count()
        
        expired = self.db.query(VosDataCache).filter(
            and_(
                VosDataCache.vos_instance_id == vos_instance_id,
                VosDataCache.expires_at < datetime.utcnow()
            )
        ).count()
        
        # 按API分组统计
        api_stats = self.db.query(
            VosDataCache.api_name,
            self.db.func.count(VosDataCache.id).label('count')
        ).filter(
            VosDataCache.vos_instance_id == vos_instance_id
        ).group_by(
            VosDataCache.api_name
        ).all()
        
        return {
            'total': total,
            'valid': valid,
            'expired': expired,
            'invalid': total - valid,
            'by_api': [{'api': name, 'count': count} for name, count in api_stats]
        }

