from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from data.data_mods import ManagePlatformUserAdd
from data.sql_client import execute_db_query, get_db
from data.redis_client import RedisClient, get_redis
from services.manage_admin_guard import verify_admin_with_permission

router = APIRouter()


@router.post("/manage_platform_user_add")
async def manage_platform_user_add(
    body: ManagePlatformUserAdd,
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
        exist = await execute_db_query(db, "select user from manage_user where user = %s", (body.new_user,))
        if exist:
            return {"current": False, "msg": "用户名已存在"}
        role_ok = await execute_db_query(db, "SELECT id FROM manage_role WHERE id = %s", (body.role_id,))
        if not role_ok:
            return {"current": False, "msg": "角色不存在"}
        await execute_db_query(
            db,
            "insert into manage_user (user, password, role_id) values (%s, %s, %s)",
            (body.new_user, body.new_password, body.role_id),
        )
        return {"current": True, "msg": "添加成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
