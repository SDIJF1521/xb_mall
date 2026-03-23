from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from data.data_mods import ManageRoleDelete
from data.redis_client import RedisClient, get_redis
from data.sql_client import execute_db_query, get_db
from services.manage_admin_guard import verify_admin_with_permission

router = APIRouter()


@router.post("/manage_role_delete")
async def manage_role_delete(
    body: ManageRoleDelete,
    access_token: str = Header(...),
    db: Connection = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.user.role"
        )
        if not ok:
            return {"current": False, "msg": msg}
        if body.role_id == 1:
            return {"current": False, "msg": "不能删除系统内置角色"}
        cnt = await execute_db_query(
            db, "SELECT COUNT(*) FROM manage_user WHERE role_id = %s", (body.role_id,)
        )
        if cnt and int(cnt[0][0]) > 0:
            return {"current": False, "msg": "仍有账号绑定该角色"}
        await execute_db_query(db, "DELETE FROM manage_role WHERE id = %s", (body.role_id,))
        return {"current": True, "msg": "已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
