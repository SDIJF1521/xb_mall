from fastapi import APIRouter, Depends, Header, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.data_mods import ManageAdBannerUpdate

router = APIRouter()


@router.patch('/manage_ad_banner_update')
async def manage_ad_banner_update(
    body: ManageAdBannerUpdate,
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """平台端：更新轮播图排序或启用状态"""
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.system_settings"
        )
        if not ok:
            return {"current": False, "msg": msg}

        sets = []
        params = []
        if body.sort_order is not None:
            sets.append("sort_order = %s")
            params.append(body.sort_order)
        if body.is_active is not None:
            sets.append("is_active = %s")
            params.append(body.is_active)

        if not sets:
            return {"current": False, "msg": "无更新字段"}

        params.append(body.banner_id)
        await execute_db_query(
            db,
            f"UPDATE ad_banner SET {', '.join(sets)} WHERE id = %s",
            tuple(params)
        )

        cache = CacheService(redis)
        await cache.delete_pattern("ad:banner:*")

        return {"current": True, "msg": "更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
