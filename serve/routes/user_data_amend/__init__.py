from typing import Annotated

import aiomysql
from fastapi import APIRouter, Depends,Form,HTTPException

from data.data_mods import UserInformation
from data.sql_client import get_db, execute_db_query
from data.redis_client import get_redis,RedisClient
from services.user_info_amend import UserInfoAmend
from services.user_info import UserInfo
from services.cache_service import CacheService

router = APIRouter()

@router.patch('/user_data_amend')
async def user_data_amend(data:Annotated[UserInformation,Form()], db:aiomysql.Connection = Depends(get_db),redis:RedisClient=Depends(get_redis)) -> dict:
    """
    修改用户个人信息
    """
    try:
        uploading = UserInfoAmend(nickname = data.nickname,age=data.age,sex=data.sex)
        result = await uploading.wrute(data.token)
        if result['current']:
            await execute_db_query(db,result['query'],result['params'])
            
            user_info = UserInfo(data.token)
            user_data = await user_info.token_analysis()
            if user_data.get('current'):
                cache = CacheService(redis)
                cache_key = cache._make_key('user:info', user_data['user'])
                await cache.delete(cache_key)
            
            return {'msg':'信息更改成功','current':True}
        else:
            return {'msg':'信息更改失败，无法验证用户','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')