from typing import Annotated

import aiomysql
from fastapi import APIRouter, Form, HTTPException, Depends

from data.data_mods import ApplyBusiness
from services.apply_seller import ApplySeller
from services.user_info import UserInfo
from services.cache_service import CacheService
from data.sql_client import get_db, execute_db_query
from data.redis_client import get_redis,RedisClient
router = APIRouter()

@router.post('/apply_seller')
async def apply_seller( data:Annotated[ApplyBusiness,Form()], db:aiomysql.Connection = Depends(get_db),redis:RedisClient=Depends(get_redis)) -> dict:
    """
    申请成为商户
    """
    apply = ApplySeller(name=data.name, phone=data.phone, mall_name=data.mall_name, mall_describe=data.mall_describe)
    database_data = await execute_db_query(db,'select * FROM shop_apply')
    out = await apply.apply(database_data, token=data.token)
    if out['current']:
        await execute_db_query(db, out['query'], out['params'])
        
        cache = CacheService(redis)
        await cache.delete_pattern('admin:apply:seller:list:*')
        user_info = UserInfo(data.token)
        user_data = await user_info.token_analysis()
        if user_data.get('current'):
            await cache.delete(cache._make_key('user:apply:seller', user_data['user']))
        
        return {'msg': '已提交请求, 我们将在3个工作日内审核您的申请并通过短信通知您。', 'current': True}
    else:
        return {'msg': out['msg'], 'current': False}