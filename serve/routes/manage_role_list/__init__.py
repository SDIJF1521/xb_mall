from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from data.redis_client import RedisClient, get_redis
from data.sql_client import execute_db_query, get_db
from services.manage_admin_guard import verify_admin_with_permission
from services.manage_rbac import parse_permissions

router = APIRouter()


@router.get("/manage_role_list")
async def manage_role_list(
    access_token: str = Header(...),
    db: Connection = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.user.role"
        )
        if not ok:
            return {"current": False, "msg": msg, "roles": []}
        rows = await execute_db_query(
            db,
            "SELECT id, name, description, permissions, sort_order FROM manage_role ORDER BY sort_order, id",
        )
        roles = []
        for r in rows:
            roles.append(
                {
                    "id": r[0],
                    "name": r[1],
                    "description": r[2] or "",
                    "permissions": parse_permissions(r[3]),
                    "sort_order": r[4] or 0,
                }
            )
        return {"current": True, "roles": roles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
