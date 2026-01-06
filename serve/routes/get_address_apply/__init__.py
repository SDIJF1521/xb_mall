import aiomysql
from fastapi import APIRouter,Form,Depends,HTTPException

from services.user_info import UserInfo
from services.cache_service import CacheService
from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient

router = APIRouter()

@router.post('/get_address_apply')
async def get_address_apply(token:str = Form(min_length=6),db:aiomysql.Connection = Depends(get_db),redis:RedisClient=Depends(get_redis)):
    """
    获取用户默认收货地址
    """
    user_info = UserInfo(token)
    user_info_data = await user_info.token_analysis()
    if user_info_data['current']:
        cache = CacheService(redis)
        cache_key = cache._make_key('user:address:default', user_info_data['user'])
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
        
        user_data = await execute_db_query(db,'select name,phone,save,city,county,address,apply_option from user_address where user = %s and apply_option = %s',
                                           (user_info_data['user'],1))
        if user_data:
            result = {'msg':'查询成功','current':True,'data':user_data[0]}
            await cache.set(cache_key, result, expire=300)
            return result
        else:
            return {'msg':'查询失败','current':False}
    else:
        return {'msg':'token无效','current':False}