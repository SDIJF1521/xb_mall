import json
import hashlib
from datetime import datetime, date
from typing import Optional, Any, Callable
from data.redis_client import RedisClient
from services.bloom_filter import BloomFilter as CustomBloomFilter

class DateTimeEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime和date对象"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

class CacheService:
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.bloom_filter = CustomBloomFilter(
            redis_client=redis_client,
            key_prefix='cache:bloom',
            capacity=10000,
            error_rate=0.001
        )
    

    def _make_key(self, prefix: str, *args) -> str:
        if not args:
            return prefix
        key_str = ':'.join(str(arg) for arg in args if arg is not None)
        if len(key_str) > 200:
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        return f"{prefix}:{key_str}"
    

    async def get(self, key: str) -> Optional[Any]:
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except:
            pass
        return None
    
    async def set(self, key: str, value: Any, expire: int = 300):
        try:
            if not hasattr(self.redis, 'redis') or self.redis.redis is None:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Redis连接未建立，跳过缓存设置 | Key: {key}")
                return
            data = json.dumps(value, ensure_ascii=False, cls=DateTimeEncoder)
            await self.redis.setex(key, expire, data)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"缓存设置失败 | Key: {key} | 错误: {str(e)}")
    
    async def delete(self, key: str):
        try:
            await self.redis.delete(key)
        except:
            pass
    
    async def delete_pattern(self, pattern: str):
        try:
            keys = await self.redis.redis.keys(pattern)
            if keys:
                await self.redis.redis.delete(*keys)
        except:
            pass

    async def get_or_set(self, key: str, func: Callable, expire: int = 300) -> Any:
        data = await self.get(key)
        if data is not None:
            return data
        result = await func()
        if result is not None:
            await self.set(key, result, expire)
        return result
    
    async def get_or_set_with_bloom(
        self, 
        key: str, 
        item_id: str, 
        func: Callable, 
        expire: int = 300,
        return_none_if_not_exists: bool = False
    ) -> Any:
        """
        带布隆过滤器检查的缓存获取方法
        先检查布隆过滤器，如果判断不存在，直接返回None，避免查询数据库
        
        Args:
            key: 缓存键
            item_id: 用于布隆过滤器检查的ID
            func: 获取数据的函数
            expire: 缓存过期时间
            return_none_if_not_exists: 如果布隆过滤器判断不存在，是否返回None
            
        Returns:
            缓存数据或函数执行结果
        """
        # 先检查缓存
        data = await self.get(key)
        if data is not None:
            return data
        
        exists = await self.bloom_filter.exists(item_id)

        if not exists and return_none_if_not_exists:
            result = await func()
            if result is None:
                await self.bloom_filter.add(item_id)
                return None
            else:
                await self.set(key, result, expire)
                await self.bloom_filter.add(item_id)
                return result
        
        result = await func()
        
        if result is not None:
            await self.set(key, result, expire)
            await self.bloom_filter.add(item_id)
        else:
            await self.bloom_filter.add(item_id)
        
        return result

