

import aiomysql
from fastapi import APIRouter,Depends,HTTPException,Query
from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient
from services.cache_service import CacheService


router = APIRouter()

@router.get('/get_address_options')
async def get_address_options(save:str = None,
                              city:str=None,
                              db:aiomysql.Connection=Depends(get_db),
                              redis:RedisClient=Depends(get_redis)):
    """
    获取省市区地址选项
    """
    try:
        cache = CacheService(redis)
        cache_key = cache._make_key('address:options', save, city)
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
        
        save_list = [i[0] for i in await execute_db_query(db,'select name from dou_area where parent_id = %s',0)]
        city_list = []
        county_list = []
        
        if not save is None:
            save_id = await execute_db_query(db,'select area_id from dou_area where name = %s',save)
            if save_id:
                city_list = [i[0] for i in await execute_db_query(db,'select name from dou_area where parent_id = %s',save_id[0][0])]
        
        if not city is None:
            city_id = await execute_db_query(db,'select area_id from dou_area where name = %s',city)
            if city_id:
                county_list = [i[0] for i in await execute_db_query(db,'select name from dou_area where parent_id = %s',city_id[0][0])]
        
        result = {
            'save_list':save_list,
            'city_list':city_list,
            'county_list':county_list
        }
        await cache.set(cache_key, result, expire=3600)
        return result
    except:
        raise HTTPException(status_code=400,detail='获取地址选项失败')