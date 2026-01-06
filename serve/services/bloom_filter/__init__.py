from typing import Optional
from data.redis_client import RedisClient

# 自定义布隆过滤器服务
class BloomFilter:

    
    def __init__(
        self, 
        redis_client: RedisClient,
        key_prefix: str = 'bloom',
        capacity: int = 1000000,
        error_rate: float = 0.001
    ):
        """
        初始化布隆过滤器
        
        Args:
            redis_client: Redis客户端实例
            key_prefix: 布隆过滤器键的前缀
            capacity: 预期容量（元素数量）
            error_rate: 误判率（0-1之间的小数）
        """
        self.redis_client = redis_client
        self.key_prefix = key_prefix
        self.capacity = capacity
        self.error_rate = error_rate
        self.filter_key = f"{key_prefix}:filter"
        self._initialized = False
        self._use_set_fallback = False
    
    async def _ensure_initialized(self):
        """确保布隆过滤器已初始化"""
        if self._initialized:
            return
        
        if self.redis_client.redis is None:
            await self.redis_client.connect()
        
        try:
            exists = await self.redis_client.redis.exists(self.filter_key)
            
            if not exists:
                try:
                    await self.redis_client.redis.execute_command(
                        'BF.RESERVE',
                        self.filter_key,
                        self.error_rate,
                        self.capacity
                    )
                    self._use_set_fallback = False
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"无法创建布隆过滤器，将使用 Set 降级方案: {str(e)}")
                    self._use_set_fallback = True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"布隆过滤器初始化检查失败，使用 Set 降级方案: {str(e)}")
            self._use_set_fallback = True
        
        self._initialized = True
    
    async def add(self, item: str) -> bool:
        """
        添加元素到布隆过滤器
        
        Args:
            item: 要添加的元素
            
        Returns:
            是否添加成功（对于布隆过滤器，通常返回 True）
        """
        await self._ensure_initialized()
        
        if self.redis_client.redis is None:
            await self.redis_client.connect()
        
        if self._use_set_fallback:
            await self.redis_client.redis.sadd(self.filter_key, item)
            return True
        
        try:
            result = await self.redis_client.redis.execute_command(
                'BF.ADD',
                self.filter_key,
                item
            )
            return bool(result)
        except Exception:
            try:
                await self.redis_client.redis.sadd(self.filter_key, item)
                return True
            except Exception:
                return False
    
    async def exists(self, item: str) -> bool:
        """
        检查元素是否存在于布隆过滤器中
        
        Args:
            item: 要检查的元素
            
        Returns:
            如果可能存在返回 True，如果一定不存在返回 False
            注意：布隆过滤器可能存在误判（假阳性），但不会有假阴性
        """
        await self._ensure_initialized()
        
        if self.redis_client.redis is None:
            await self.redis_client.connect()
        
        if self._use_set_fallback:
            result = await self.redis_client.redis.sismember(self.filter_key, item)
            return bool(result)
        
        try:
            result = await self.redis_client.redis.execute_command(
                'BF.EXISTS',
                self.filter_key,
                item
            )
            return bool(result)
        except Exception:
            try:
                result = await self.redis_client.redis.sismember(self.filter_key, item)
                return bool(result)
            except Exception:
                return False

