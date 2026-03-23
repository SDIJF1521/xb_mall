import json
from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from data.data_mods import ManageRoleSave
from data.redis_client import RedisClient, get_redis
from data.sql_client import execute_db_query, get_db
from services.manage_admin_guard import verify_admin_with_permission

router = APIRouter()


@router.post("/manage_role_save")
async def manage_role_save(
    body: ManageRoleSave,
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
        perm_json = json.dumps(body.permissions, ensure_ascii=False)
        rid = body.id
        if rid is None or rid == 0:
            await execute_db_query(
                db,
                "INSERT INTO manage_role (name, description, permissions, sort_order) VALUES (%s,%s,%s,0)",
                (body.name, body.description, perm_json),
            )
            return {"current": True, "msg": "已保存"}
        if rid == 1:
            await execute_db_query(
                db,
                "UPDATE manage_role SET name=%s, description=%s, permissions=%s WHERE id=1",
                (body.name, body.description, perm_json),
            )
            return {"current": True, "msg": "已保存"}
        await execute_db_query(
            db,
            "UPDATE manage_role SET name=%s, description=%s, permissions=%s WHERE id=%s",
            (body.name, body.description, perm_json, rid),
        )
        return {"current": True, "msg": "已保存"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
