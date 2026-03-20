"""POST /favorite_add 添加收藏（商品或店铺）"""
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header

from services.user_info import UserInfo
from services.cache_service import CacheService

from data.data_mods import FavoriteAddBody
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()


async def _resolve_user(access_token: str) -> str | None:
    user_info = UserInfo(access_token)
    token_data = await user_info.token_analysis()
    if token_data.get("current"):
        return token_data["user"]
    return None


@router.post("/favorite_add")
async def favorite_add(
    data: Annotated[FavoriteAddBody, Body()],
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}

    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    fav_type = data.type
    mall_id = data.mall_id
    shopping_id = data.shopping_id

    if fav_type not in ("commodity", "store"):
        return {"code": 400, "msg": "type 必须为 commodity 或 store", "success": False}

    if fav_type == "commodity" and not shopping_id:
        return {"code": 400, "msg": "收藏商品时 shopping_id 不能为空", "success": False}

    # 收藏名称（用于模糊搜索）
    name = ""

    if fav_type == "commodity":
        doc = await mongodb.find_one(
            "shopping",
            {"mall_id": mall_id, "shopping_id": shopping_id, "audit": 1},
        )
        if not doc:
            return {"code": 404, "msg": "商品不存在或已下架", "success": False}
        name = doc.get("name", "")

        exist = await db_pool.execute_query(
            "SELECT id FROM user_favorites "
            "WHERE user = %s AND type = 'commodity' AND mall_id = %s AND shopping_id = %s",
            (user, mall_id, shopping_id),
        )
        if exist:
            return {"code": 409, "msg": "该商品已在收藏中", "success": False}

    elif fav_type == "store":
        rows = await db_pool.execute_query(
            "SELECT mall_name FROM store WHERE mall_id = %s AND state = 1 AND state_platform = 1",
            (mall_id,),
        )
        if not rows:
            return {"code": 404, "msg": "店铺不存在或已关闭", "success": False}
        name = rows[0][0] or ""

        exist = await db_pool.execute_query(
            "SELECT id FROM user_favorites "
            "WHERE user = %s AND type = 'store' AND mall_id = %s AND (shopping_id IS NULL OR shopping_id = 0)",
            (user, mall_id),
        )
        if exist:
            return {"code": 409, "msg": "该店铺已在收藏中", "success": False}

    await db_pool.execute_query(
        "INSERT INTO user_favorites (user, type, mall_id, shopping_id, name) "
        "VALUES (%s, %s, %s, %s, %s)",
        (user, fav_type, mall_id, shopping_id if fav_type == "commodity" else None, name),
    )

    cache = CacheService(redis)
    await cache.delete(cache._make_key("favorites", user))

    return {"code": 200, "msg": "收藏成功", "success": True}
