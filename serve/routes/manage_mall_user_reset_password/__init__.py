import logging

import aiomysql
from fastapi import APIRouter, Depends, Form, HTTPException

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post('/manage_mall_user_reset_password')
async def manage_mall_user_reset_password(
    token: str = Form(..., min_length=6),
    username: str = Form(..., min_length=1),
    new_password: str = Form(..., min_length=8, max_length=40),
    db: aiomysql.Connection = Depends(get_db),
    redis_client: RedisClient = Depends(get_redis),
):
    """管理员重置商城用户密码"""
    try:
        ok, msg, admin_user = await verify_admin_with_permission(
            db, redis_client, token, required="admin.user.mall"
        )
        if not ok:
            return {"current": False, "msg": msg}

        has_digit = any(c.isdigit() for c in new_password)
        has_letter = any(c.isalpha() for c in new_password)
        if not (has_digit and has_letter):
            return {"current": False, "msg": "密码必须包含数字和字母"}

        user_rows = await execute_db_query(
            db, "SELECT user FROM `user` WHERE user = %s", (username,)
        )
        if not user_rows:
            return {"current": False, "msg": "用户不存在"}

        await execute_db_query(
            db, "UPDATE `user` SET password = %s WHERE user = %s",
            (new_password, username)
        )

        await redis_client.delete(f"user_{username}")

        cache = CacheService(redis_client)
        await cache.delete(cache._make_key("user:info", username))

        return {"current": True, "msg": "密码重置成功"}
    except Exception as e:
        logger.error(f"manage_mall_user_reset_password error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
