"""GET /store_commodity_list 获取指定店铺的上架商品列表（分页，无需登录）"""
import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends

from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.file_client import read_file_base64_with_cache
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.data_mods import StoreCommodityListQuery
from services.cache_service import CacheService

router = APIRouter()


@router.get("/store_commodity_list")
async def store_commodity_list(
    params: Annotated[StoreCommodityListQuery, Depends()],
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """获取指定店铺的上架商品列表，支持分页和名称搜索，无需登录"""
    store_rows = await db_pool.execute_query(
        "SELECT mall_id FROM store WHERE mall_id = %s AND state = 1 AND state_platform = 1",
        (params.mall_id,),
    )
    if not store_rows:
        return {"code": 404, "msg": "店铺不存在或已关闭", "success": False, "data": [], "total": 0}

    search_kw = (params.search or "").strip()
    offset = (params.page - 1) * params.page_size

    mongo_filter: dict = {"mall_id": params.mall_id, "audit": 1}
    if search_kw:
        mongo_filter["name"] = {"$regex": search_kw, "$options": "i"}

    total = await mongodb.count_documents("shopping", mongo_filter)
    if total == 0:
        return {
            "code": 200,
            "msg": "成功",
            "success": True,
            "data": [],
            "total": 0,
            "page": params.page,
            "page_size": params.page_size,
        }

    docs = await mongodb.find_many(
        "shopping",
        mongo_filter,
        skip=offset,
        limit=params.page_size,
        sort=[("shopping_id", -1)],
    )

    async def _build_item(doc: dict) -> dict:
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

    items = await asyncio.gather(*[_build_item(d) for d in docs])

    return {
        "code": 200,
        "msg": "成功",
        "success": True,
        "data": list(items),
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
    }
