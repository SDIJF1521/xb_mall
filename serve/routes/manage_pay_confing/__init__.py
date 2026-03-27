from fastapi import APIRouter, Depends, Header, HTTPException

from services.manage_admin_guard import verify_admin_with_permission

from data.sql_client import get_db
from data.redis_client import RedisClient, get_redis

router = APIRouter()


@router.patch('/manage_pay_confing')
async def manage_pay_confing(
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.system_settings"
        )
        if not ok:
            return {"current": False, "msg": msg}
        return {"current": True, "msg": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
