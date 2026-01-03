from typing import List, Tuple, Optional, Dict, Any
from typing import List, Tuple, Optional
from config.redis_config import settings

# 延迟导入 aioredis，避免 Windows 多进程导入问题
_aioredis = None

def _get_aioredis():
    """延迟导入 aioredis 模块"""
    global _aioredis
    if _aioredis is None:
        import aioredis
        _aioredis = aioredis
    return _aioredis

class RedisClient:
    def __init__(self, redis_url: Optional[str] = None, db: Optional[int] = None):
        """初始化Redis客户端"""
        # 如果未提供参数，则使用配置文件中的默认值
        self.redis_url = redis_url or settings.REDIS_URL
        self.db = db if db is not None else settings.REDIS_DB
        self.redis = None

        
    async def connect(self) -> None:
        """异步连接到Redis服务器"""
        # 延迟导入 aioredis，避免 Windows 多进程导入问题
        aioredis = _get_aioredis()
        self.redis = await aioredis.from_url(
            self.redis_url,
            db=self.db,
            encoding=settings.REDIS_ENCODING,
            decode_responses=settings.REDIS_DECODE_RESPONSES,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
            health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL
        )

    async def close(self) -> None:
        """异步关闭Redis连接"""
        if self.redis:
            await self.redis.close()
            if hasattr(self.redis, 'wait_closed'):
                await self.redis.wait_closed()
            else:
                # 对于旧版本aioredis，可能需要使用await self.redis.close()
                await self.redis.close()
    
    async def set(self,key: str, value: str) -> None:
        """设置键值对"""
        await self.redis.set(key, value)

    async def setex(self, key: str, timeout: int, value: str) -> None:
        """设置带过期时间的键值对"""
        await self.redis.setex(key, timeout, value)

    async def get(self, key: str) -> Optional[str]:
        """获取键对应的值"""
        return await self.redis.get(key)

    async def delete(self, key: str) -> int:
        """删除键"""
        return await self.redis.delete(key)

    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间"""
        return await self.redis.ttl(key)
    
    async def hset(self, name: str, key: str, value: str) -> int:
        """设置哈希表中的字段值"""
        return await self.redis.hset(name, key, value)

    async def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希表中的字段值"""
        return await self.redis.hget(name, key)

    async def hgetall(self, name: str) -> Dict[str, str]:
        """获取哈希表中的所有字段和值"""
        return await self.redis.hgetall(name)

    async def hdel(self, name: str, *keys: str) -> int:
        """删除哈希表中的一个或多个字段"""
        return await self.redis.hdel(name, *keys)

    async def hexists(self, name: str, key: str) -> bool:
        """检查哈希表中是否存在指定字段"""
        return await self.redis.hexists(name, key)

    async def hlen(self, name: str) -> int:
        """获取哈希表中的字段数量"""
        return await self.redis.hlen(name)

    async def hkeys(self, name: str) -> List[str]:
        """获取哈希表中的所有字段名"""
        return await self.redis.hkeys(name)

    async def hvals(self, name: str) -> List[str]:
        """获取哈希表中的所有字段值"""
        return await self.redis.hvals(name)

    async def hscan(self, name: str, cursor: int = 0, count: int = 100) -> Tuple[int, Dict[str, str]]:
        """增量扫描哈希表中的字段"""
        return await self.redis.hscan(name, cursor=cursor, count=count)

    async def hmset(self, name: str, mapping: Dict[str, str]) -> None:
        """批量设置哈希表中的多个字段值"""
        # 注意：aioredis的hmset在新版本中已被hset替代，使用方式略有不同
        if not mapping:
            return
        await self.redis.hset(name, mapping=mapping)

    async def execute_pipeline(self, commands: List[Tuple[str, Tuple]]) -> List:
        """
        执行Redis Pipeline批量命令
        
        Args:
            commands: 命令列表，每个命令格式为 (方法名, (参数1, 参数2, ...))
        
        Returns:
            命令执行结果列表
        """
        if self.redis is None:
            raise RuntimeError("Redis客户端未连接")
        
        async with self.redis.pipeline() as pipe:
            for cmd, args in commands:
                # 动态调用Redis连接的方法（如 setex, get 等）
                getattr(pipe, cmd)(*args)
            return await pipe.execute()
        
def get_redis():
# 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client