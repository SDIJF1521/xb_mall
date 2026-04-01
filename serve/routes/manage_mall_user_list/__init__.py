import base64
import logging
from typing import Optional

import aiomysql
from fastapi import APIRouter, Depends, Form, Query, HTTPException

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


@router.get('/manage_mall_user_list')
async def manage_mall_user_list(
    token: str = Query(..., min_length=6),
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    status: Optional[int] = Query(None, description="0正常 1冻结"),
    merchant: Optional[int] = Query(None, description="0买家 1卖家"),
    db: aiomysql.Connection = Depends(get_db),
    redis_client: RedisClient = Depends(get_redis),
):
    """平台端 — 商城用户分页列表（含搜索 / 筛选）"""
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis_client, token, required="admin.user.mall"
        )
        if not ok:
            return {"current": False, "msg": msg}

        await _ensure_status_column(db)

        where_clauses = []
        params = []

        if keyword:
            where_clauses.append("(u.user LIKE %s OR u.email LIKE %s)")
            like = f"%{keyword}%"
            params.extend([like, like])

        if status is not None:
            where_clauses.append("u.status = %s")
            params.append(status)

        if merchant is not None:
            where_clauses.append("u.merchant = %s")
            params.append(merchant)

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        count_sql = f"SELECT COUNT(*) FROM `user` u{where_sql}"
        total_rows = await execute_db_query(db, count_sql, tuple(params))
        total = total_rows[0][0] if total_rows else 0

        offset = (page - 1) * page_size
        data_sql = (
            f"SELECT u.user, u.email, u.merchant, u.time, u.status "
            f"FROM `user` u{where_sql} "
            f"ORDER BY u.time DESC "
            f"LIMIT %s OFFSET %s"
        )
        rows = await execute_db_query(db, data_sql, tuple(params + [page_size, offset]))

        user_list = []
        for row in rows:
            time_val = row[3]
            if time_val is not None:
                time_val = str(time_val)
            user_list.append({
                "username": row[0],
                "email": row[1],
                "merchant": row[2],
                "register_time": time_val,
                "status": row[4] if len(row) > 4 else 0,
            })

        return {
            "current": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "user_list": user_list,
        }
    except Exception as e:
        logger.error(f"manage_mall_user_list error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
