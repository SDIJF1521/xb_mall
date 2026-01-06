from typing import Annotated

import aiomysql
from fastapi import APIRouter,Form,Depends, HTTPException

from services.user_info import UserInfo
from services.cache_service import CacheService
from data.data_mods import UserAddressModify
from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient

router = APIRouter()

@router.patch('/modify_address')
async def modify_address(data:Annotated[UserAddressModify,Form()],db:aiomysql.Connection=Depends(get_db),redis:RedisClient=Depends(get_redis)):
    """
    修改用户收货地址
    """
    try:
        token_user_info = UserInfo(token=data.token)
        token_user_data = await token_user_info.token_analysis()
        if token_user_data['current']:
            sql_address = await execute_db_query(db,'select user from user_address where address_id = %s',data.id)
            if sql_address:
                if sql_address[0][0] == token_user_data['user']:
                    await execute_db_query(db,'update user_address set save = %s,city = %s,county = %s,address = %s,name = %s,phone = %s where address_id = %s',
                                            (data.save,data.city,data.county,data.address,data.name,data.phone,data.id))
                    cache = CacheService(redis)
                    await cache.delete(cache._make_key('user:address', token_user_data['user']))
                    return {'msg':'修改成功','current':True}
                else:
                    return {'msg':'该用户还没有相关地址数据','current':False}
            else:
                return {'msg':'没有相关地址信息','current':False}
        else:
            raise HTTPException(status_code=401, detail="未授权")
    except Exception as e:
          raise HTTPException(status_code=500,detail=str(e))
