from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from data.data_mods import ManagePlatformUserRole
from data.redis_client import RedisClient, get_redis
from data.sql_client import execute_db_query, get_db
from services.manage_admin_guard import verify_admin_with_permission

router = APIRouter()


@router.post("/manage_platform_user_role")
async def manage_platform_user_role(
    body: ManagePlatformUserRole,
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
        role_ok = await execute_db_query(db, "SELECT id FROM manage_role WHERE id = %s", (body.role_id,))
        if not role_ok:
            return {"current": False, "msg": "角色不存在"}
        tgt = await execute_db_query(db, "SELECT user FROM manage_user WHERE user = %s", (body.target_user,))
        if not tgt:
            return {"current": False, "msg": "用户不存在"}
        await execute_db_query(
            db, "UPDATE manage_user SET role_id = %s WHERE user = %s",
            (body.role_id, body.target_user),
        )
        await redis.delete(f"admin_{body.target_user}")
        await redis.delete(f"admin_refresh_{body.target_user}")
        return {"current": True, "msg": "角色已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
