"""DELETE /shopping_cart_delete 删除购物车商品"""
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query

from services.user_info import UserInfo
from services.verify_duter_token import VerifyDuterToken
from services.cache_service import CacheService

from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis

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


@router.delete("/shopping_cart_delete")
async def shopping_cart_delete(
    id: int = Query(..., description="购物车项 ID"),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
):
    """删除指定购物车商品（需为当前用户自己的项）"""
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}

    user = await _resolve_user(access_token, redis)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    rows = await db_pool.execute_query(
        "SELECT id FROM shopping_cart WHERE id = %s AND user = %s",
        (id, user),
    )
    if not rows:
        return {"code": 404, "msg": "购物车项不存在或已删除", "success": False}

    await db_pool.execute_query("DELETE FROM shopping_cart WHERE id = %s AND user = %s", (id, user))

    cache = CacheService(redis)
    await cache.delete(cache._make_key("shopping_cart", user))

    return {"code": 200, "msg": "删除成功", "success": True}
