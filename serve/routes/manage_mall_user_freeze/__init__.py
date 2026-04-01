import logging

import aiomysql
from fastapi import APIRouter, Depends, Form, HTTPException

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

router = APIRouter()
logger = logging.getLogger(__name__)

ENSURE_STATUS_COLUMN = """
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME   = 'user'
      AND COLUMN_NAME  = 'status'
"""
ALTER_ADD_STATUS = "ALTER TABLE `user` ADD COLUMN `status` TINYINT NOT NULL DEFAULT 0 COMMENT '0正常 1冻结' AFTER `time`"


async def _ensure_status_column(db: aiomysql.Connection):
    rows = await execute_db_query(db, ENSURE_STATUS_COLUMN)
    if rows and rows[0][0] == 0:
        await execute_db_query(db, ALTER_ADD_STATUS)


@router.post('/manage_mall_user_freeze')
async def manage_mall_user_freeze(
    token: str = Form(..., min_length=6),
    username: str = Form(..., min_length=1),
    action: str = Form(..., pattern=r'^(freeze|unfreeze)$'),
    db: aiomysql.Connection = Depends(get_db),
    redis_client: RedisClient = Depends(get_redis),
):
    """冻结或解冻商城用户。action: freeze / unfreeze"""
    try:
        ok, msg, admin_user = await verify_admin_with_permission(
            db, redis_client, token, required="admin.user.mall"
        )
        if not ok:
            return {"current": False, "msg": msg}

        await _ensure_status_column(db)

        user_rows = await execute_db_query(
            db, "SELECT user, status FROM `user` WHERE user = %s", (username,)
        )
        if not user_rows:
            return {"current": False, "msg": "用户不存在"}

        current_status = user_rows[0][1] if len(user_rows[0]) > 1 else 0
        target_status = 1 if action == "freeze" else 0

        if current_status == target_status:
            label = "已被冻结" if target_status == 1 else "未被冻结"
            return {"current": False, "msg": f"该用户{label}，无需重复操作"}

        await execute_db_query(
            db, "UPDATE `user` SET status = %s WHERE user = %s",
            (target_status, username)
        )

        cache = CacheService(redis_client)
        if action == "freeze":
            await redis_client.delete(f"user_{username}")

        await cache.delete_pattern("admin:user:list")
        await cache.delete(cache._make_key("user:data", username))
        await cache.delete(cache._make_key("user:info", username))

        label = "冻结" if action == "freeze" else "解冻"
        return {"current": True, "msg": f"{label}成功"}
    except Exception as e:
        logger.error(f"manage_mall_user_freeze error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
