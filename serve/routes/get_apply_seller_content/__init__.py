import aiomysql
from fastapi import APIRouter, Depends, HTTPException, Form

from data.sql_client import get_db, execute_db_query
from data.redis_client import get_redis,RedisClient
from services.apply_seller_conten import ApplySellerConten
from services.user_info import UserInfo
from services.cache_service import CacheService

router = APIRouter()

@router.post('/get_apply_seller_content')
async def get_apply_seller_content(token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db),redis:RedisClient=Depends(get_redis)):
    """
    获取用户商户申请详情
    """
    try:
        apply = ApplySellerConten(token= token)
        user = UserInfo(token)
        name = await user.token_analysis()
        if name['current']:
            cache = CacheService(redis)
            cache_key = cache._make_key('user:apply:seller', name['user'])
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
            
            sql_data = await execute_db_query(db,'SELECT * FROM shop_apply WHERE user = %s',name['user'])
            reject_cause = None
            out = await apply.content(sql_data)
            if out['state'] == 2:
                reject_cause_sql = await execute_db_query(db,'SELECT * FROM rejection_reason WHERE user = %s',name['user'])
                if reject_cause_sql:
                    reject_cause = reject_cause_sql[0][1]
            result = {
                'name':out['name'],
                'phone':out['phone'],
                'mall_name':out['mall_name'],
                'mall_describe':out['mall_describe'],
                'reject_cause':reject_cause,
                'current':True
            }
            await cache.set(cache_key, result, expire=300)
            return result
        else:
            return {'msg':'token验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")