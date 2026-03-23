from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from data.sql_client import execute_db_query, get_db
from data.redis_client import RedisClient, get_redis
from services.manage_admin_guard import verify_admin_with_permission

router = APIRouter()


@router.get("/manage_platform_user_list")
async def manage_platform_user_list(
    access_token: str = Header(...),
    db: Connection = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db,
            redis,
            access_token,
            required_any=["admin.user.platform", "admin.user.role"],
        )
        if not ok:
            return {"current": False, "msg": msg, "user_list": []}
        rows = await execute_db_query(
            db,
            """SELECT u.`user`, u.role_id, r.name
               FROM manage_user u
               LEFT JOIN manage_role r ON u.role_id = r.id
               ORDER BY u.`user`""",
        )
        user_list = [
            {"user": r[0], "role_id": r[1], "role_name": r[2] or ""} for r in rows
        ]
        return {"current": True, "user_list": user_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
