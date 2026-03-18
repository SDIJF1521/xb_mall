"""GET /mall_commodity_search 商城商品搜索（模糊匹配名称、描述、标签、店铺名称，任一符合即可，分页，无需登录）"""
import asyncio
import logging
import re
from typing import Annotated

from fastapi import APIRouter, Depends

from data.data_mods import MallCommoditySearchQuery
from data.file_client import read_file_base64_with_cache
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.redis_client import RedisClient, get_redis
from data.sql_client_pool import db_pool
from services.cache_service import CacheService

router = APIRouter()
logger = logging.getLogger(__name__)


async def _build_output_item(doc: dict, redis: RedisClient) -> dict:
    """根据 MongoDB 文档构建输出格式"""
    img_b64 = ""
    if doc.get("img_list"):
        img_b64 = await read_file_base64_with_cache(doc["img_list"][0], redis, cache_expire=3600) or ""
    spec_list = doc.get("specification_list") or []
    price = float(spec_list[0].get("price", 0)) if spec_list else 0
    info = doc.get("info", "")
    return {
        "mall_id": doc["mall_id"],
        "shopping_id": doc["shopping_id"],
        "name": doc.get("name", ""),
        "info": info[:50] + "..." if len(info) > 50 else info,
        "type": doc.get("type", []),
        "price": price,
        "img": img_b64,
    }


@router.get("/mall_commodity_search")
async def mall_commodity_search(
    params: Annotated[MallCommoditySearchQuery, Depends()],
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """
    商城商品搜索：模糊匹配商品名称、描述、标签、店铺名称，任一符合即返回。
    分页默认 50 条，无需登录。
    """
    keyword = (params.keyword or "").strip()

    if not keyword:
        return {
            "code": 200,
            "msg": "成功",
            "success": True,
            "data": [],
            "total": 0,
            "page": params.page,
            "page_size": params.page_size,
        }

    cache = CacheService(redis)
    cache_key = cache._make_key("mall_commodity_search", keyword, params.page, params.page_size)
    cached = await cache.get(cache_key)
    if cached:
        return cached

    try:
        # 获取有效店铺的 mall_id 列表（state=1, state_platform=1）
        valid_store_rows = await db_pool.execute_query(
            "SELECT mall_id FROM store WHERE state = 1 AND state_platform = 1",
            (),
        )
        valid_mall_ids = [r[0] for r in valid_store_rows] if valid_store_rows else []
        if not valid_mall_ids:
            return {
                "code": 200,
                "msg": "成功",
                "success": True,
                "data": [],
                "total": 0,
                "page": params.page,
                "page_size": params.page_size,
            }

        # 按店铺名称模糊匹配获取 mall_id
        store_name_rows = await db_pool.execute_query(
            "SELECT mall_id FROM store WHERE mall_name LIKE %s AND state = 1 AND state_platform = 1",
            (f"%{keyword}%",),
        )
        mall_ids_by_store_name = [r[0] for r in store_name_rows] if store_name_rows else []

        # 转义正则特殊字符，防止注入
        regex_safe = re.escape(keyword)

        # 构建 MongoDB $or 条件：名称、描述、标签、店铺名称任一匹配
        or_conditions = [
            {"name": {"$regex": regex_safe, "$options": "i"}},
            {"info": {"$regex": regex_safe, "$options": "i"}},
            {"type": {"$regex": regex_safe, "$options": "i"}},
        ]
        if mall_ids_by_store_name:
            or_conditions.append({"mall_id": {"$in": mall_ids_by_store_name}})

        mongo_filter = {
            "$and": [
                {"audit": 1},
                {"mall_id": {"$in": valid_mall_ids}},
                {"$or": or_conditions},
            ]
        }

        total = await mongodb.count_documents("shopping", mongo_filter)
        if total == 0:
            result = {
                "code": 200,
                "msg": "成功",
                "success": True,
                "data": [],
                "total": 0,
                "page": params.page,
                "page_size": params.page_size,
            }
            await cache.set(cache_key, result, expire=60)
            return result

        offset = (params.page - 1) * params.page_size
        docs = await mongodb.find_many(
            "shopping",
            mongo_filter,
            skip=offset,
            limit=params.page_size,
            sort=[("shopping_id", -1)],
        )

        items = await asyncio.gather(*[_build_output_item(d, redis) for d in docs])

        result = {
            "code": 200,
            "msg": "成功",
            "success": True,
            "data": list(items),
            "total": total,
            "page": params.page,
            "page_size": params.page_size,
        }
        await cache.set(cache_key, result, expire=60)
        return result

    except Exception as e:
        logger.error("商城商品搜索异常 | keyword=%s | 错误: %s", keyword, str(e), exc_info=True)
        return {
            "code": 500,
            "msg": "搜索失败",
            "success": False,
            "data": [],
            "total": 0,
            "page": params.page,
            "page_size": params.page_size,
        }
