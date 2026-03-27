from fastapi import APIRouter, Depends, Header, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.data_mods import ManageAdBannerDelete

router = APIRouter()


@router.delete('/manage_ad_banner_delete')
async def manage_ad_banner_delete(
    body: ManageAdBannerDelete,
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """平台端：删除轮播图广告"""
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.system_settings"
        )
        if not ok:
            return {"current": False, "msg": msg}

        row = await execute_db_query(
            db, "SELECT id FROM ad_banner WHERE id = %s", (body.banner_id,)
        )
        if not row:
            return {"current": False, "msg": "轮播图不存在"}

        await execute_db_query(db, "DELETE FROM ad_banner WHERE id = %s", (body.banner_id,))

        cache = CacheService(redis)
        await cache.delete_pattern("ad:banner:*")

        return {"current": True, "msg": "删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
