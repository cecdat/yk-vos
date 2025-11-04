"""
Redis缓存工具
提供快速的内存缓存，用于存储频繁访问的数据
"""
import json
import logging
from typing import Optional, Any
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis连接池（单例）
_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> Optional[redis.Redis]:
    """获取Redis客户端（单例模式）"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # 测试连接
            _redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败，将不使用Redis缓存: {e}")
            _redis_client = None
    return _redis_client


class RedisCache:
    """Redis缓存工具类"""
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """从Redis获取数据"""
        try:
            client = get_redis_client()
            if client is None:
                return None
            data = client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis获取数据失败 {key}: {e}")
            return None
    
    @staticmethod
    def set(key: str, value: Any, ttl: int = 300) -> bool:
        """设置Redis缓存（默认5分钟）"""
        try:
            client = get_redis_client()
            if client is None:
                return False
            client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"Redis设置数据失败 {key}: {e}")
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """删除Redis缓存"""
        try:
            client = get_redis_client()
            if client is None:
                return False
            client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis删除数据失败 {key}: {e}")
            return False
    
    @staticmethod
    def exists(key: str) -> bool:
        """检查key是否存在"""
        try:
            client = get_redis_client()
            if client is None:
                return False
            return client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis检查key失败 {key}: {e}")
            return False

