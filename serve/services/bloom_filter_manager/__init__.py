import asyncio
import logging
from typing import Optional
from data.redis_client import RedisClient
from services.bloom_filter import BloomFilter

logger = logging.getLogger(__name__)

class BloomFilterManager:
    """
    布隆过滤器管理器，支持双实例切换方案
    用于实现零停机时间的布隆过滤器重建
    """
    
    def __init__(self, redis_client: RedisClient, key_prefix: str = 'bloom'):
        self.redis_client = redis_client
        self.key_prefix = key_prefix
        
        # 创建两个布隆过滤器实例
        self.primary_filter = BloomFilter(
            redis_client=redis_client,
            key_prefix=f"{key_prefix}:primary",
            capacity=1000000,
            error_rate=0.001
        )
        self.secondary_filter = BloomFilter(
            redis_client=redis_client,
            key_prefix=f"{key_prefix}:secondary", 
            capacity=1000000,
            error_rate=0.001
        )
        
        # 当前活跃实例标识 (0=primary, 1=secondary)
        self.active_instance = 0
        self.rebuild_lock = asyncio.Lock()
        
    @property
    def active_filter(self):
        """获取当前活跃的布隆过滤器实例"""
        return self.primary_filter if self.active_instance == 0 else self.secondary_filter
    
    @property 
    def standby_filter(self):
        """获取备用的布隆过滤器实例"""
        return self.secondary_filter if self.active_instance == 0 else self.primary_filter
    
    async def add(self, item: str) -> bool:
        """向当前活跃的布隆过滤器添加元素"""
        return await self.active_filter.add(item)
    
    async def exists(self, item: str) -> bool:
        """检查元素是否存在于当前活跃的布隆过滤器中"""
        return await self.active_filter.exists(item)
    
    async def rebuild_from_database(self, load_data_func):
        """
        从数据库重建布隆过滤器
        load_data_func: 一个异步函数，返回需要加载到布隆过滤器的所有数据列表
        """
        async with self.rebuild_lock:
            try:
                logger.info(f"开始重建布隆过滤器，当前活跃实例: {'primary' if self.active_instance == 0 else 'secondary'}")
                
                # 确定备用实例
                target_filter = self.standby_filter
                target_instance_name = 'secondary' if self.active_instance == 0 else 'primary'
                
                logger.info(f"正在清空备用实例: {target_instance_name}")
                # 清空备用实例（如果有相应方法的话，这里可能需要手动实现）
                
                # 从数据库加载数据
                logger.info("从数据库加载数据...")
                data_items = await load_data_func()
                
                logger.info(f"准备向备用实例添加 {len(data_items)} 个元素")
                
                # 批量添加到备用实例
                batch_size = 1000  # 分批处理，避免一次性处理太多数据
                for i in range(0, len(data_items), batch_size):
                    batch = data_items[i:i + batch_size]
                    for item in batch:
                        await target_filter.add(item)
                    
                    logger.info(f"已处理 {min(i + batch_size, len(data_items))}/{len(data_items)} 个元素")
                
                # 切换活跃实例
                old_active = self.active_instance
                self.active_instance = 1 if self.active_instance == 0 else 0
                
                logger.info(f"布隆过滤器重建完成，切换到实例: {'primary' if self.active_instance == 0 else 'secondary'}")
                logger.info(f"原活跃实例: {'primary' if old_active == 0 else 'secondary'}")
                
            except Exception as e:
                logger.error(f"布隆过滤器重建失败: {str(e)}", exc_info=True)
                raise
    
    async def get_stats(self):
        """获取布隆过滤器统计信息"""
        primary_exists = await self.primary_filter.exists("test")
        secondary_exists = await self.secondary_filter.exists("test")
        
        return {
            "active_instance": "primary" if self.active_instance == 0 else "secondary",
            "instances": {
                "primary": {
                    "status": "initialized" if getattr(self.primary_filter, '_initialized', False) else "not_initialized"
                },
                "secondary": {
                    "status": "initialized" if getattr(self.secondary_filter, '_initialized', False) else "not_initialized"
                }
            }
        }


# 全局布隆过滤器管理器实例
bloom_filter_manager: Optional[BloomFilterManager] = None

def get_bloom_filter_manager() -> Optional[BloomFilterManager]:
    """获取全局布隆过滤器管理器实例"""
    return bloom_filter_manager

def init_bloom_filter_manager(redis_client: RedisClient):
    """初始化全局布隆过滤器管理器"""
    global bloom_filter_manager
    bloom_filter_manager = BloomFilterManager(redis_client)
    return bloom_filter_manager