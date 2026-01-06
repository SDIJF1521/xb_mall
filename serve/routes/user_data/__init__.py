import aiomysql

from fastapi import APIRouter,Depends,Form,HTTPException

from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient
from services.user_info import UserInfo
from services.cache_service import CacheService

router = APIRouter()

@router.post('/user_data')
async def user_data(token:str = Form(min_length=6),db:aiomysql.Connection = Depends(get_db),redis:RedisClient=Depends(get_redis)):
    """获取用户基础数据"""
    user_info = UserInfo(token)
    user_info_data = await user_info.token_analysis()
    if user_info_data['current']:
        cache = CacheService(redis)
        cache_key = cache._make_key('user:data', user_info_data['user'])
        
        # 防止缓存穿透
        async def fetch_user_data():
            user_data = await execute_db_query(db,'select * from user where user = %s',user_info_data['user'])
            if user_data:
                return {'msg':'查询成功','current':True,'data':[user_data[0][0],user_data[0][3]]}
            return None
        
        result = await cache.get_or_set_with_bloom(
            key=cache_key,
            item_id=f"user:{user_info_data['user']}",  # 用于布隆过滤器检查
            func=fetch_user_data,
            expire=300,
            return_none_if_not_exists=True  # 如果布隆过滤器判断不存在，返回None
        )
        
        if result:
            return result
        else:
            return {'msg':'查询失败','current':False}
    else:
        return {'msg':'token无效','current':False}