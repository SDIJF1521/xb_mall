from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from config.manage_permission_catalog import PERMISSION_CATALOG
from data.redis_client import RedisClient, get_redis
from data.sql_client import get_db
from services.manage_admin_guard import verify_admin_with_permission

router = APIRouter()


@router.get("/manage_permission_catalog")
async def manage_permission_catalog(
    access_token: str = Header(...),
    db: Connection = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.user.role"
        )
        if not ok:
            return {"current": False, "msg": msg, "catalog": []}
        return {"current": True, "catalog": PERMISSION_CATALOG}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
