from datetime import date

import aiomysql
from fastapi import APIRouter, Form, Depends, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient, get_redis

router = APIRouter()

@router.post('/today_user_list')
async def today_user_list(token:str=Form(min_length=6),db:aiomysql.Connection = Depends(get_db),redis_client:RedisClient=Depends(get_redis)):
    """
    获取今日注册用户列表
    """
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis_client, token, required="admin.dashboard"
        )
        if not ok:
            return {"current": False, "msg": msg}

        cache = CacheService(redis_client)
        today_str = str(date.today())
        cache_key = cache._make_key('admin:today:user', today_str)
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
        
        query = 'SELECT * FROM user WHERE time = %s'
        params = (date.today(),)
        result = await execute_db_query(db,query,params)
        result_data = {'user_list':[i[0] for i in result],'current':True}
        await cache.set(cache_key, result_data, expire=300)
        return result_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
