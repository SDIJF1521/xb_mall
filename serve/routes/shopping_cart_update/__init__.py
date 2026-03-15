"""PATCH /shopping_cart_update 修改购物车商品数量"""
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header

from services.user_info import UserInfo
from services.verify_duter_token import VerifyDuterToken
from services.cache_service import CacheService

from data.data_mods import ShoppingCartUpdateBody
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()


async def _resolve_user(access_token: str, redis: RedisClient) -> str | None:
    """解析 token 获取用户标识"""
    user_info = UserInfo(access_token)
    token_data = await user_info.token_analysis()
    if token_data.get("current"):
        return token_data["user"]
    verify = VerifyDuterToken(access_token, redis)
    payload = await verify.token_data()
    if payload and payload.get("user"):
        return payload["user"]
    return None


@router.patch("/shopping_cart_update")
async def shopping_cart_update(
    data: Annotated[ShoppingCartUpdateBody, Body()],
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """修改购物车商品数量，校验库存"""
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}

    user = await _resolve_user(access_token, redis)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    cart_id = data.id
    new_quantity = data.quantity

    # 查询购物车项，校验归属
    rows = await db_pool.execute_query(
        "SELECT id, mall_id, shopping_id, specification_id FROM shopping_cart WHERE id = %s AND user = %s",
        (cart_id, user),
    )
    if not rows:
        return {"code": 404, "msg": "购物车项不存在或已删除", "success": False}

    mall_id, shopping_id, specification_id = rows[0][1], rows[0][2], rows[0][3]

    # 从 MongoDB 获取商品库存
    doc = await mongodb.find_one(
        "shopping",
        {"mall_id": mall_id, "shopping_id": shopping_id},
    )
    if not doc:
        return {"code": 404, "msg": "商品已下架", "success": False}

    spec_list = doc.get("specification_list") or []
    spec = next(
        (s for s in spec_list if s.get("specification_id") == specification_id),
        spec_list[0] if spec_list else {},
    )
    stock = int(spec.get("stock", 0))

    if new_quantity > stock:
        return {"code": 400, "msg": f"库存不足，当前仅剩 {stock} 件", "success": False}

    await db_pool.execute_query(
        "UPDATE shopping_cart SET quantity = %s WHERE id = %s AND user = %s",
        (new_quantity, cart_id, user),
    )

    cache = CacheService(redis)
    await cache.delete(cache._make_key("shopping_cart", user))

    return {"code": 200, "msg": "修改成功", "success": True}
