from typing import Annotated

import aiomysql
from fastapi import APIRouter, Form,Depends,HTTPException, status

from data.sql_client import get_db,execute_db_query
from data.data_mods import GetApplySellerUser
from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

def get_redis():
    from main import redis_client
    return redis_client

router = APIRouter()

@router.post('/get_apply_seller_user')
async def get_apply_seller_user(data:Annotated[GetApplySellerUser,Form()],db:aiomysql.Connection = Depends(get_db),redis_client=Depends(get_redis)):
    """
    管理员按名称查询商户申请
    """
    try:
        verify = ManagementTokenVerify(token=data.token,redis_client=redis_client)
        sql_data = await execute_db_query(db,'select user from manage_user')
        verify_data = await verify.run(sql_data)
        if verify_data['current']:
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
        else:
            return {'current':False,'msg':'token验证失败'}
    except Exception as e:
       HTTPException(status_code=500, detail=str(e))
