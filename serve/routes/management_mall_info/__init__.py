import base64
from typing import Annotated

import aiomysql
from fastapi import APIRouter,Form,Depends

from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient
from data.data_mods import ManagementGetMall


def get_redis():
    from main import redis_client
    return redis_client

router = APIRouter()

@router.post('/management_mall_info')
async def MallInfo(data:Annotated[ManagementGetMall,Form()],db:aiomysql.Connection=Depends(get_db),redis_client=Depends(get_redis)):
    """
    管理员获取商户信息
    """
    token_verify = ManagementTokenVerify(redis_client=redis_client,token=data.token)
    sql_admin_list = await execute_db_query(db,'select user from manage_user')
    verify_data = await token_verify.run(sql_admin_list)
    if verify_data['current']:
        cache = CacheService(redis_client)
        cache_key = cache._make_key('admin:mall:info', data.name)
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
        
        sql_mall_data = await execute_db_query(db,'select * from mall_info where user = %s',data.name) 
        if  sql_mall_data:
            img = await execute_db_query(db,'select HeadPortrait from personal_details where user = %s',data.name)

            try:
                if img:
                    with open(img[0][0],'rb') as f:
                        mall_info = list(sql_mall_data[0])
                        mall_info.append(base64.b64encode(f.read()).decode('utf-8'))
                else:
                    with open('./img/通用/通用.png','rb') as f:
                        mall_info = list(sql_mall_data[0])
                        mall_info.append(base64.b64encode(f.read()).decode('utf-8'))
                result = {'msg':'获取成功','current':True,'mall_info':mall_info}
                await cache.set(cache_key, result, expire=300)
                return result
            except:
                mall_info = list(sql_mall_data[0])
                mall_info.append('')
                result = {'msg':'获取成功','current':True,'mall_info':mall_info}
                await cache.set(cache_key, result, expire=300)
                return result
        else:
            return {'msg':'该用户不为商家','current':False}
    else:
        return {'msg':'token失效','current':False}



