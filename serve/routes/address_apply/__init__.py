from typing import Annotated

import aiomysql
from fastapi import APIRouter,Depends,Form,HTTPException
from services.user_info import UserInfo
from services.cache_service import CacheService
from data.data_mods import UserAddressApply
from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient

router = APIRouter()

@router.post('/address_apply')
async def address_apply(data:Annotated[UserAddressApply,Form()],db:aiomysql.Connection=Depends(get_db),redis:RedisClient=Depends(get_redis)):
    """
    设置默认收货地址
    逻辑：同一用户只能有一个默认地址（apply_option=1）
    """
    user_info = UserInfo(token=data.token)
    user = await user_info.token_analysis()
    try:
        if user['current']:
            sql_data = await execute_db_query(db,'SELECT * FROM user_address WHERE address_id = %s and user = %s',(data.id,user['user']))
            if sql_data:
                await execute_db_query(db,'UPDATE user_address SET apply_option = %s WHERE user = %s',(0,user['user']))
                await execute_db_query(db,'UPDATE user_address SET apply_option = %s WHERE address_id = %s and user = %s',(1,data.id,user['user']))
                
                cache = CacheService(redis)
                await cache.delete(cache._make_key('user:address', user['user']))
                await cache.delete(cache._make_key('user:address:default', user['user']))
                
                return {'current':True,'msg':'应用成功'}
            else:
                raise HTTPException(status_code=401, detail="没有改相关数据")
        else:
            raise HTTPException(status_code=401, detail="未授权")
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e)) 