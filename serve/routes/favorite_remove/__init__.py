"""DELETE /favorite_remove 移除收藏"""
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query

from services.user_info import UserInfo
from services.cache_service import CacheService

from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis

router = APIRouter()


async def _resolve_user(access_token: str) -> str | None:
    user_info = UserInfo(access_token)
    token_data = await user_info.token_analysis()
    if token_data.get("current"):
        return token_data["user"]
    return None


@router.delete("/favorite_remove")
async def favorite_remove(
    id: int = Query(..., description="收藏记录ID"),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
):
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}

    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    rows = await db_pool.execute_query(
        "SELECT id FROM user_favorites WHERE id = %s AND user = %s",
        (id, user),
    )
    if not rows:
        return {"code": 404, "msg": "收藏记录不存在或已删除", "success": False}

    await db_pool.execute_query(
        "DELETE FROM user_favorites WHERE id = %s AND user = %s",
        (id, user),
    )

    cache = CacheService(redis)
    await cache.delete(cache._make_key("favorites", user))

    return {"code": 200, "msg": "已取消收藏", "success": True}
