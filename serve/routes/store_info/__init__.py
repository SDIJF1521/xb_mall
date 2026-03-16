"""GET /store_info 获取面向用户展示的店铺信息（无需登录）"""
from fastapi import APIRouter, Depends, Query

from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.file_client import read_file_base64_with_cache
from services.cache_service import CacheService

router = APIRouter()


@router.get("/store_info")
async def store_info(
    mall_id: int = Query(..., ge=1, description="店铺ID"),
    redis: RedisClient = Depends(get_redis),
):
    """获取店铺展示信息（店铺名称、介绍、联系方式、图片等），无需登录"""
    cache = CacheService(redis)
    cache_key = cache._make_key("store_page_info", mall_id)

    cached = await cache.get(cache_key)
    if cached:
        return cached

    rows = await db_pool.execute_query(
        "SELECT mall_id, mall_name, mall_phone, mall_site, mall_describe, img_path, creation_time, state "
        "FROM store WHERE mall_id = %s AND state = 1 AND state_platform = 1",
        (mall_id,),
    )
    if not rows:
        return {"code": 404, "msg": "店铺不存在或已关闭", "success": False, "data": None}

    row = rows[0]
    img_b64 = ""
    if row[5]:
        img_b64 = await read_file_base64_with_cache(row[5], redis, cache_expire=3600) or ""

    data = {
        "mall_id": row[0],
        "mall_name": row[1],
        "phone": row[2],
        "site": row[3],
        "info": row[4],
        "img": img_b64,
        "create_time": str(row[6]) if row[6] else "",
    }

    result = {"code": 200, "msg": "成功", "success": True, "data": data}
    await cache.set(cache_key, result, expire=300)
    return result
