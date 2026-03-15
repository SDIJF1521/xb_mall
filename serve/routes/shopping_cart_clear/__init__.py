"""DELETE /shopping_cart_clear 清空当前用户购物车"""
from typing import Annotated

from fastapi import APIRouter, Depends, Header

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


@router.delete("/shopping_cart_clear")
async def shopping_cart_clear(
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
):
    """清空当前用户购物车（删除该用户全部购物车项）"""
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}

    user = await _resolve_user(access_token, redis)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    # 先统计数量用于提示
    count_rows = await db_pool.execute_query(
        "SELECT COUNT(*) FROM shopping_cart WHERE user = %s",
        (user,),
    )
    total = int(count_rows[0][0]) if count_rows else 0
    if total == 0:
        return {"code": 200, "msg": "购物车已为空", "success": True, "deleted": 0}

    await db_pool.execute_query(
        "DELETE FROM shopping_cart WHERE user = %s",
        (user,),
    )

    cache = CacheService(redis)
    await cache.delete(cache._make_key("shopping_cart", user))

    return {"code": 200, "msg": "已清空购物车", "success": True, "deleted": total}
