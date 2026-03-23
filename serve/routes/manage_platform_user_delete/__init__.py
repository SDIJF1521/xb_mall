from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from data.data_mods import ManagePlatformUserDelete
from data.sql_client import execute_db_query, get_db
from data.redis_client import RedisClient, get_redis
from services.manage_admin_guard import verify_admin_with_permission

router = APIRouter()


@router.post("/manage_platform_user_delete")
async def manage_platform_user_delete(
    body: ManagePlatformUserDelete,
    access_token: str = Header(...),
    db: Connection = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    try:
        ok, msg, me = await verify_admin_with_permission(
            db, redis, access_token, required="admin.user.platform"
        )
        if not ok:
            return {"current": False, "msg": msg}
        if body.target_user == me:
            return {"current": False, "msg": "不能删除当前登录账号"}
        await execute_db_query(db, "delete from manage_user where user = %s", (body.target_user,))
        await redis.delete(f"admin_{body.target_user}")
        await redis.delete(f"admin_refresh_{body.target_user}")
        return {"current": True, "msg": "已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
