from typing  import Annotated

import aiomysql
from fastapi import APIRouter,Depends,Form,HTTPException

from services.user_info import UserInfo
from services.cache_service import CacheService
from data.data_mods import UserDeleteAddress
from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient

router = APIRouter()

@router.delete('/delete_address')
async def delete_address(data:Annotated[UserDeleteAddress,Form()],db:aiomysql.Connection=Depends(get_db),redis:RedisClient=Depends(get_redis)):
    """
    删除用户收货地址
    """
    try:
        user_info = UserInfo(data.token)
        user = await user_info.token_analysis()
        if not user['current']:
            raise HTTPException(status_code=401,detail='用户不存在')
        
        sql_data = await execute_db_query(db,'select * from user_address where address_id = %s and user = %s',(data.id,user['user']))

        if sql_data:
            await execute_db_query(db,'delete from user_address where address_id = %s and user = %s',(data.id,user['user']))
            cache = CacheService(redis)
            await cache.delete(cache._make_key('user:address', user['user']))
            return {'msg':'删除成功','current':True}
        else:
            raise HTTPException(status_code=401,detail='没有相关信息')
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
