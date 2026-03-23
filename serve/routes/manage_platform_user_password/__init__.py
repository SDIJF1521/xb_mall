from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from data.data_mods import ManagePlatformUserPassword
from data.sql_client import execute_db_query, get_db
from data.redis_client import RedisClient, get_redis
from services.manage_admin_guard import verify_admin_with_permission

router = APIRouter()


@router.post("/manage_platform_user_password")
async def manage_platform_user_password(
    body: ManagePlatformUserPassword,
    access_token: str = Header(...),
    db: Connection = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.user.platform"
        )
        if not ok:
            return {"current": False, "msg": msg}
        tgt = await execute_db_query(db, "select user from manage_user where user = %s", (body.target_user,))
        if not tgt:
            return {"current": False, "msg": "用户不存在"}
        await execute_db_query(
            db,
            "update manage_user set password = %s where user = %s",
            (body.new_password, body.target_user),
        )
        await redis.delete(f"admin_{body.target_user}")
        await redis.delete(f"admin_refresh_{body.target_user}")
        return {"current": True, "msg": "密码已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
