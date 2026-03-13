import math
import hashlib
from struct import unpack, pack
from typing import Optional, List
from data.redis_client import RedisClient

import logging
logger = logging.getLogger(__name__)


def _make_hashfuncs(num_slices: int, num_bits: int):
    """生成布隆过滤器所需的哈希函数组"""
    if num_bits >= (1 << 31):
        fmt_code, chunk_size = 'Q', 8
    elif num_bits >= (1 << 15):
        fmt_code, chunk_size = 'I', 4
    else:
        fmt_code, chunk_size = 'H', 2
    total_hash_bits = 8 * num_slices * chunk_size
    if total_hash_bits > 384:
        hashfn = hashlib.sha512
    elif total_hash_bits > 256:
        hashfn = hashlib.sha384
    elif total_hash_bits > 160:
        hashfn = hashlib.sha256
    elif total_hash_bits > 128:
        hashfn = hashlib.sha1
    else:
        hashfn = hashlib.md5
    fmt = fmt_code * (hashfn().digest_size // chunk_size)
    num_salts, extra = divmod(num_slices, len(fmt))
    if extra:
        num_salts += 1
    salts = tuple(hashfn(hashfn(pack('I', i)).digest()) for i in range(num_salts))

    def _compute_hashes(key: str):
        key_bytes = key.encode('utf-8') if isinstance(key, str) else str(key).encode('utf-8')
        i = 0
        for salt in salts:
            h = salt.copy()
            h.update(key_bytes)
            for uint in unpack(fmt, h.digest()):
                yield uint % num_bits
                i += 1
                if i >= num_slices:
                    return

    return _compute_hashes


class BloomFilter:
    """布隆过滤器（基于 RedisClient setbit/getbit 实现，无需 aioredis/aiobloom）"""

    def __init__(
        self,
        redis_client: RedisClient,
        key_prefix: str = 'bloom',
        capacity: int = 1_000_000,
        error_rate: float = 0.001
    ):
        if not (0 < error_rate < 1):
            raise ValueError("error_rate 必须在 0 到 1 之间")
        if capacity <= 0:
            raise ValueError("capacity 必须大于 0")

        self.redis_client = redis_client
        self.filter_key = f"{key_prefix}:filter"

        num_slices = int(math.ceil(math.log(1.0 / error_rate, 2)))
        bits_per_slice = int(math.ceil(
            (capacity * abs(math.log(error_rate))) /
            (num_slices * (math.log(2) ** 2))
        ))
        self.num_slices = num_slices
        self.bits_per_slice = bits_per_slice
        self.num_bits = num_slices * bits_per_slice
        self._make_hashes = _make_hashfuncs(num_slices, self.bits_per_slice)

    def _get_bit_indexes(self, item: str) -> List[int]:
        """计算元素在位图中的所有位索引"""
        indexes = []
        offset = 0
        for hash_val in self._make_hashes(item):
            indexes.append(offset + hash_val)
            offset += self.bits_per_slice
        return indexes

    async def add(self, item: str) -> bool:
        """
        添加元素到布隆过滤器

        Returns:
            True 表示添加成功
        """
        if self.redis_client.redis is None:
            await self.redis_client.connect()

        indexes = self._get_bit_indexes(item)
        try:
            async with self.redis_client.redis.pipeline() as pipe:
                for idx in indexes:
                    pipe.setbit(self.filter_key, idx, 1)
                await pipe.execute()
            return True
        except Exception as e:
            logger.warning(f"布隆过滤器 add 失败 | Key: {self.filter_key} | Item: {item} | 错误: {e}")
            return False

    async def clear(self) -> bool:
        """
        清空布隆过滤器（删除 Redis 中的位图 key）

        Returns:
            True 表示清空成功
        """
        if self.redis_client.redis is None:
            await self.redis_client.connect()

        try:
            await self.redis_client.redis.delete(self.filter_key)
            logger.info(f"布隆过滤器已清空 | Key: {self.filter_key}")
            return True
        except Exception as e:
            logger.warning(f"布隆过滤器 clear 失败 | Key: {self.filter_key} | 错误: {e}")
            return False

    async def exists(self, item: str) -> bool:
        """
        检查元素是否可能存在于布隆过滤器中

        Returns:
            True 表示可能存在，False 表示一定不存在
        """
        if self.redis_client.redis is None:
            await self.redis_client.connect()

        indexes = self._get_bit_indexes(item)
        try:
            async with self.redis_client.redis.pipeline() as pipe:
                for idx in indexes:
                    pipe.getbit(self.filter_key, idx)
                results = await pipe.execute()
            return all(results)
        except Exception as e:
            logger.warning(f"布隆过滤器 exists 失败 | Key: {self.filter_key} | Item: {item} | 错误: {e}")
            return False
