
import aiomysql
from fastapi import APIRouter,Depends,HTTPException

from services.on_line import OnLine
from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService
from data.sql_client import execute_db_query,get_db
from data.redis_client import RedisClient, get_redis

router = APIRouter()

@router.get('/get_online_user_list')
async def get_online_user_list(token,redis_client:RedisClient=Depends(get_redis),db:aiomysql.Connection = Depends(get_db)):
    """
    管理员获取在线用户列表
    """
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis_client, token, required="admin.dashboard"
        )
        if not ok:
            return {"current": False, "msg": msg}

        cache = CacheService(redis_client)
        cache_key = 'admin:online:user:list'
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data

        online = OnLine(redis_client=redis_client)
        data = await online.get_online_users()
        await cache.set(cache_key, data, expire=10)
        return data
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
