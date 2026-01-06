import aiomysql
from fastapi import APIRouter,HTTPException,Depends,Form

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService


router = APIRouter()

@router.post('/user_list')
async def user_list(token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db),redis_client:RedisClient = Depends(get_redis)):
    """
    获取所有用户列表
    """
    try:
        Verify = ManagementTokenVerify(token=token,redis_client=redis_client)

        data = await execute_db_query(db,'select user from manage_user')
        Verify_data = await Verify.run(data=data)
        if Verify_data['current']:
            cache = CacheService(redis_client)
            cache_key = 'admin:user:list'
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
            
            query = 'SELECT user FROM user'
            result = await execute_db_query(db,query)
            user_list = [i[0] for i in result]
            result_data = {'user_list':user_list,"current":True}
            await cache.set(cache_key, result_data, expire=300)
            return result_data
        else:
            return {'msg':'token验证失败',"current":False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))