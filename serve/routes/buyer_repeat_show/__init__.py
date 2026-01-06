from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form

from services.verify_duter_token import VerifyDuterToken
from services.cache_service import CacheService

from data.data_mods import AddMallData
from data.redis_client import RedisClient,get_redis
from data.sql_client import get_db,execute_db_query


router = APIRouter()

@router.post('/buyer_repeat_show')
async def check_mall_name(data:Annotated[AddMallData,Form()],db:Connection=Depends(get_db),redis:RedisClient=Depends(get_redis)):
    """
    检查店铺是否重复
    """
    try:
        verify = VerifyDuterToken(token=data.token,redis_client=redis)
        verify_data = await verify.token_data()
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(verify_data.get('user')))
        verify_val = await verify.verify_token(sql_data)
        if verify_data.get('station') == '1':
            if verify_val[0]:
                cache = CacheService(redis)
                cache_key = cache._make_key('mall:repeat', data.user, data.mall_name, data.mall_phone, data.mall_site, data.info)
                cached_data = await cache.get(cache_key)
                if cached_data:
                    return cached_data
                
                sql_mall_data = await execute_db_query(db,
                                                    "select user from store where user = %s and mall_name = %s and mall_phone = %s and mall_site = %s and mall_describe = %s",
                                                    (data.user,data.mall_name,data.mall_phone,data.mall_site,data.info))
                if sql_mall_data:
                    result = {"code": 200,"msg":"该店铺已存在",'current':True}
                else:
                    result = {"code": 200,"msg":"该店铺不存在",'current':False}
                await cache.set(cache_key, result, expire=300)
                return result
            else:
                return {"code": 400,"msg":"token过期",'current':False}
        else:
            return {"code": 400,"msg":"权限不足",'current':False}
    except Exception as e:
        return {"code": 500,"msg":str(e),'current':False}
            