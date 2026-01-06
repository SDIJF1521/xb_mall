import aiofiles
import base64
import os
import asyncio
from typing import Optional
from services.cache_service import CacheService
from data.redis_client import RedisClient

async def read_file_async(file_path: str) -> Optional[bytes]:
    """异步读取文件内容"""
    if not file_path or not os.path.exists(file_path):
        return None
    try:
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    except:
        return None

async def read_file_base64_async(file_path: str) -> str:
    """异步读取文件并转换为Base64编码"""
    content = await read_file_async(file_path)
    if content:
        return base64.b64encode(content).decode('utf-8')
    return ''

async def read_file_base64_with_cache(file_path: str, redis_client: RedisClient, cache_expire: int = 3600) -> str:
    """异步读取文件并转换为Base64编码（带缓存）"""
    if not file_path:
        return ''
    cache = CacheService(redis_client)
    cache_key = cache._make_key('img_base64', file_path)
    # 先查缓存
    cached_data = await cache.get(cache_key)
    if cached_data:
        return cached_data
    # 读取文件
    base64_str = await read_file_base64_async(file_path)
    # 缓存结果
    if base64_str:
        await cache.set(cache_key, base64_str, expire=cache_expire)
    return base64_str

async def read_files_base64_batch(file_paths: list, redis_client: RedisClient, cache_expire: int = 3600) -> list:
    """批量异步读取文件并转换为Base64编码（带缓存）"""
    tasks = [read_file_base64_with_cache(path, redis_client, cache_expire) for path in file_paths]
    return await asyncio.gather(*tasks)

