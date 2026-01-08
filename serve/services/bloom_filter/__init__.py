import logging
from typing import Optional, Any
from data.redis_client import RedisClient
from config.redis_config import settings

logger = logging.getLogger(__name__)


class BloomFilter:
    """布隆过滤器服务（基于 aiobloom）"""
    
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
        self._bloom_filter: Optional[Any] = None
        self._initialized = False
    
    def _get_redis_url_for_aiobloom(self) -> str:
        """获取 aiobloom 需要的 Redis URL 格式（host:port）"""
        return f"{settings.REDIS_HOST}:{settings.REDIS_PORT}"
    
    async def _ensure_initialized(self):
        """确保布隆过滤器已初始化"""
        if self._initialized:
            return
        
        from aiobloom.aiobloom import BloomFilter as AioBloomFilter
        
        if self.redis_client.redis is None:
            await self.redis_client.connect()
        
        self._bloom_filter = AioBloomFilter(
            capacity=self.capacity,
            error_rate=self.error_rate,
            bloom_key=self.filter_key
        )
        redis_url = self._get_redis_url_for_aiobloom()
        await self._bloom_filter.connect(redis_url=redis_url)
        
        self._initialized = True
    
    async def add(self, item: str) -> bool:
        """
        添加元素到布隆过滤器
        
        Args:
            item: 要添加的元素
            
        Returns:
            是否添加成功
        """
        await self._ensure_initialized()
        
        if self._bloom_filter is None:
            raise RuntimeError("布隆过滤器未初始化")
        
        result = await self._bloom_filter.add(item)
        return bool(result)
    
    async def exists(self, item: str) -> bool:
        """
        检查元素是否存在于布隆过滤器中
        
        Args:
            item: 要检查的元素
            
        Returns:
            如果可能存在返回 True，如果一定不存在返回 False
        """
        await self._ensure_initialized()
        
        if self._bloom_filter is None:
            raise RuntimeError("布隆过滤器未初始化")
        
        result = await self._bloom_filter.exist(item)
        return bool(result)

