from typing import Annotated

import aiomysql
from fastapi import APIRouter, Form,Depends,HTTPException, status

from data.sql_client import get_db,execute_db_query
from data.data_mods import GetApplySellerUser
from data.redis_client import RedisClient, get_redis
from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

router = APIRouter()

@router.post('/get_apply_seller_user')
async def get_apply_seller_user(data:Annotated[GetApplySellerUser,Form()],db:aiomysql.Connection = Depends(get_db),redis_client:RedisClient=Depends(get_redis)):
    """
    管理员按名称查询商户申请
    """
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis_client, data.token, required="admin.audit_seller"
        )
        if not ok:
            return {"current": False, "msg": msg}

        cache = CacheService(redis_client)
        cache_key = cache._make_key('admin:apply:seller:search', data.name)
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
        
        result = await execute_db_query(db,'select * from shop_apply where name=%s',data.name)
        if result:
            result_data = {'current':True,'apply_list':[list(i) for i in result]}
        else:
            result_data = {'current':False,'msg':'未查询到该用户的申请'}
        await cache.set(cache_key, result_data, expire=60)
        return result_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
