from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from data.redis_client import RedisClient, get_redis
from data.sql_client import get_db
from services.manage_admin_guard import verify_admin_with_permission
from services.manage_rbac import get_user_permissions, get_user_role_row

router = APIRouter()


@router.get("/manage_session")
async def manage_session(
    access_token: str = Header(...),
    db: Connection = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    try:
        ok, msg, username = await verify_admin_with_permission(db, redis, access_token)
        if not ok or not username:
            return {"current": False, "msg": msg}
        perms = await get_user_permissions(db, username)
        rr = await get_user_role_row(db, username)
        return {
            "current": True,
            "user": username,
            "permissions": perms,
            "role_id": rr[0] if rr else None,
            "role_name": rr[1] if rr else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
